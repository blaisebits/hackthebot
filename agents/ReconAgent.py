from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.HostUpdate import host_update, get_stub_host
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_recon_prompt_template, get_output_format_prompt_template, get_task_answer_prompt_template
from utils.States import StingerState, Host
from utils.Tasking import get_new_task

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
recon_tool_node = ToolNode(rb_tools)

def recon_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    task_str = None
    agent_messages = []
    context = []

    # Tasking workflow:
    #  Checking if working -> proceed to tool calling again
    #  Check if validated -> check for next task
    #  Check if new -> do preflightcheck and tool calls.
    if not state["tasks"][state["current_task"]]["agent"] == "Recon": # Not assigned to Recon
        state["current_task"] = get_new_task("Recon", state["tasks"])

    if state["tasks"][state["current_task"]]["agent"] == "Recon": # Task assigned to Recon
        if state["tasks"][state["current_task"]]["status"] == "working": # Task is working
            task_str = state["tasks"][state["current_task"]]["task"]
            target_ip = state["tasks"][state["current_task"]]["target_ip"]
            context.append(state["hosts"][target_ip])
            agent_messages.append(AIMessage(f"ReconAgent: Reworking task {state["current_task"]}: \"{task_str}\"."))

        elif (state["tasks"][state["current_task"]]["status"] == "validated"
              or state["tasks"][state["current_task"]]["status"] == "new"): # task is validated/new

            if state["tasks"][state["current_task"]]["status"] == "validated":
                state["current_task"] = get_new_task("Recon", state["tasks"])
                if state["current_task"] == -1: #No more tasks for this agent
                    return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution. Passing to Stinger.")]}

            task_str = state["tasks"][state["current_task"]]["task"]
            target_ip = state["tasks"][state["current_task"]]["target_ip"]
            state["tasks"][state["current_task"]]["status"] = "working"
            agent_messages.append(AIMessage(f"ReconAgent: Starting new task {state["current_task"]}: \"{task_str}\"."))

            if not state["tasks"][state["current_task"]]["preflightcheck"]: # No PFC yet
                if state["tasks"][state["current_task"]]["target_ip"] in state["hosts"].keys():  # Target IP has entry in host table
                    agent_messages.append(AIMessage(
                        f"EnumAgent: Sending task {state["current_task"]}: \"{task_str}\" to validator for pre-flight check."))
                    return {
                        "messages": agent_messages,
                        "current_task": state["current_task"]
                    }
                else:
                    # Add blank entry to host table
                    target_host = get_stub_host(state["tasks"][state["current_task"]]["target_ip"])

                    state["hosts"][target_host["ip_address"]] = target_host
                    state["tasks"][state["current_task"]]["preflightcheck"] = True
                    task_str = state["tasks"][state["current_task"]]["task"]
            context.append(state["hosts"][target_ip])

        else: #No tasks available, routing back to Stinger
            return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution. Passing to Stinger.")]}

    ## Setting up LLM Call
    if task_str is not None:

        recon_prompt_template = get_recon_prompt_template()
        recon_prompt = recon_prompt_template.invoke(
            {
                "tasks": task_str,
                "context": context
            }
        )

        response = llm_with_tools.invoke(recon_prompt)
        state["tasks"][state["current_task"]]["tool"].append(response.tool_calls[0]["name"])
        agent_messages.append(response)
        return {
            "messages": agent_messages,
            "tasks": state["tasks"],
            "current_task": state["current_task"],
            "hosts": state["hosts"]
        }
    else:
        # return no tasks response
        return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def recon_router(state: StingerState):
    last_message = state["messages"][-1]
    current_task = state["tasks"][state["current_task"]]
    preflightcheck = current_task["preflightcheck"]

    if last_message.tool_calls: return "ReconToolNode"
    if not preflightcheck: return "ReconValidator"

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
        state["tasks"][ state["current_task"] ]["output"].append(output)

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
    state["tasks"][state["current_task"]]["preflightcheck"] = True
    target_ip = state["tasks"][state["current_task"]]["target_ip"]
    validator_prompt_template = get_task_answer_prompt_template()
    validator_prompt = validator_prompt_template.invoke(
        {
            "task": state["tasks"][ state["current_task"] ]["task"],
            "host_data": state["hosts"][ target_ip ]
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

recon_workflow.add_conditional_edges("ReconAgent", recon_router, ["ReconToolNode", "ReconHandoff", "ReconValidator"])
recon_workflow.add_node("ReconToolNode", recon_tool_node)
recon_workflow.add_node("ReconHandoff", handoff)

recon_workflow.add_edge("ReconToolNode", "ReconOutputFormatter")
recon_workflow.add_node("ReconOutputFormatter", output_formatter)

recon_workflow.add_edge("ReconOutputFormatter", "HostUpdate")
recon_workflow.add_node("HostUpdate", host_update)

recon_workflow.add_edge("HostUpdate", "ReconValidator")
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
#   "messages": [
#     {
#       "content": "foobar",
#       "type": "human"
#     }
#   ],
#   "hosts": {
#     "a": "b"
#   },
#   "tasks": [
#     {
#       "task": "Find common open ports on 127.0.0.1.",
#       "target_ip": "127.0.0.1",
#       "status": "New",
#       "recon": "Recon",
#       "tool": [],
#       "output": [],
#       "answer": {
#         "question": "",
#         "answer": ""
#       }
#     }
#   ],
#   "current_task": 0,
#   "context": "",
#   "next": ""
# }
