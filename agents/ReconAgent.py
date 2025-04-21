from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_recon_prompt_template, get_output_format_prompt_template, get_task_answer_prompt_template
from utils.States import StingerState, Host

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
recon_tool_node = ToolNode(rb_tools)

def recon_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    context = ""
    task_call = None

    current_task = state["tasks"][state["current_task"]]
    is_new_task = current_task["status"] == "new"
    is_working_task = current_task["status"] == "working"
    is_validated_task = current_task["status"] == "validated"
    is_assigned_recon = current_task["agent"] = "Recon"

    if is_assigned_recon and not is_validated_task:
        task_call = current_task["task"]
        if is_working_task:
            context = [
                state["context"],
                current_task["output"]
            ]
        if is_new_task:
            state["tasks"][ state["current_task" ]]["status"] = "working"
            context = [
                state["context"]
            ]
    else:
        for index, task in enumerate(state["tasks"]):  #Find the first 'new' task
            if task["agent"] == "Recon":
                if task["status"] == "new":  # The task hasn't been executed
                    task_call = task["task"]
                    state["tasks"][index]["status"] = "working" # Mark task as executing
                    state["current_task"] = index
                    break # stopping at first 'new' task

    if task_call is not None:
        recon_prompt_template = get_recon_prompt_template()
        recon_prompt = recon_prompt_template.invoke(
            {
                "tasks": task_call,
                "context": context
            }
        )

        response = llm_with_tools.invoke(recon_prompt)
        state["tasks"][state["current_task"]]["tool"].append(response.tool_calls[0]["name"])

        return {
            "messages": [response],
            "tasks": state["tasks"],
            "current_task": state["current_task"]
        }
    else:
        # return no tasks response
        return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def recon_router(state: StingerState):
    last_message = state["messages"][-1]

    if last_message.type == 'ai' and last_message.tool_calls:
        return "ReconToolNode"
    return "ReconHandoff"

def output_formatter(state: StingerState):
    last_message = state["messages"][-1]
    if last_message.type == 'tool':
        llm_output_format_selection = llm.bind_tools(tool_parsers)
        tool_output = last_message.content

        output_format_prompt_template = get_output_format_prompt_template()
        output_format_prompt = output_format_prompt_template.invoke(
            {
                "tool_output": tool_output
            }
        )

        response = llm_output_format_selection.invoke(output_format_prompt)
        state["messages"] = add_messages(state["messages"], response)
        output  = response.tool_calls[0]["args"]

        target_host = Host(
            ip_address= output["ip_address"],
            hostname= [output["hostname"]],
            ports= {}
        )

        #commit host data to the state table
        state["hosts"][f"{target_host["hostname"]}({target_host["ip_address"]})"] = target_host
        state["tasks"][ state["current_task"] ]["output"].append(output)
        # state["tasks"][ state["current_task"] ]["status"] = "completed"

        return {
            "messages": state["messages"],
            "hosts": state["hosts"],
            "tasks": state["tasks"]
        }
    else:
        return {
            "messages": [AIMessage("ReconOutPutFormatter: No tool output, passing to ReconAgent.")]
        }


def validator(state: StingerState):
    validator_prompt_template = get_task_answer_prompt_template()
    validator_prompt = validator_prompt_template.invoke(
        {
            "task": state["tasks"][ state["current_task"] ]["task"],
            "tool_output": state["tasks"][ state["current_task"] ]["output"]
        }
    )

    llm_with_structured_output = llm.with_structured_output(TaskAnswer)
    response = llm_with_structured_output.invoke(validator_prompt)

    if response.answer == "":    # Check if task needs further processing from blank answer
        return {
            "messages": [AIMessage("ReconValidator: Task unanswered, passing to ReconAgent.")]
        }
    else:
        state["tasks"][ state["current_task"] ]["status"] = "validated"
        state["tasks"][ state["current_task"] ]["answer"] = response

        return {
            "messages": [AIMessage(f"ReconValidator: Task {state["current_task"]} validated.\n"
                                   f"Question: {response.question}\n"
                                   f"Answer: {response.answer}\n")],
            "tasks": state["tasks"]
        }


def handoff(state: StingerState):
    """Hand off back to stinger"""
    return Command(
        goto="StingerAgent",
        update=state,
        graph=Command.PARENT
    )

# Defining the agent graph
recon_workflow = StateGraph(StingerState)

recon_workflow.add_edge(START, "ReconAgent")
recon_workflow.add_node("ReconAgent", recon_agent)

recon_workflow.add_conditional_edges("ReconAgent", recon_router, ["ReconToolNode", "ReconHandoff"])
recon_workflow.add_node("ReconToolNode", recon_tool_node)
recon_workflow.add_node("ReconHandoff", handoff)

recon_workflow.add_edge("ReconToolNode", "ReconOutputFormatter")
recon_workflow.add_node("ReconOutputFormatter", output_formatter)

recon_workflow.add_edge("ReconOutputFormatter", "ReconValidator")
recon_workflow.add_node("ReconValidator", validator)

recon_workflow.add_edge("ReconValidator", "ReconAgent")

recon_graph = recon_workflow.compile()

if __name__ == "__main__":
    config = Configuration
    test_state = StingerState(
        tasks=[{"task":"Find common open ports on 127.0.0.1.",
                "status":"new",
                "agent": "Recon"}],
        hosts={},
        context="",
        messages=[HumanMessage("Find common open ports on 127.0.0.1")],
        next= ""
    )

    recon_graph.invoke(test_state, {"recursion_limit": 6})

# {
#   "tasks": [{"task":"Find common open ports on 127.0.0.1.","status":"new","agent":"Recon"}],
#   "hosts": {},
#   "context": "",
#   "messages": [
#     {
#       "content": "Find common open ports on 127.0.0.1.",
#       "type": "human"
#     }
#   ]
# }
