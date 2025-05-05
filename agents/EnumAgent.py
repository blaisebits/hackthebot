from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.HostUpdate import host_update, get_stub_host
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_enum_prompt_template, get_output_format_prompt_template, get_task_answer_prompt_template
from utils.States import StingerState, Host
from utils.Tasking import get_new_task

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
enum_tool_node = ToolNode(rb_tools)


def enum_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    task_str = None
    agent_messages = []
    context = []

    # Tasking workflow:
    #  Checking if working -> proceed to tool calling again
    #  Check if validated -> check for next task
    #  Check if new -> do preflightcheck and tool calls.
    if not state["tasks"][state["current_task"]]["agent"] == "Enum":  # Not assigned to Enum
        state["current_task"] = get_new_task("Enum", state["tasks"])

    if state["tasks"][state["current_task"]]["agent"] == "Enum":  # Task assigned to Enum
        if state["tasks"][state["current_task"]]["status"] == "working":  # Task is working
            task_str = state["tasks"][state["current_task"]]["task"]
            target_ip = state["tasks"][state["current_task"]]["target_ip"]
            context.append(state["hosts"][target_ip])
            agent_messages.append(AIMessage(f"EnumAgent: Reworking task {state["current_task"]}: \"{task_str}\"."))

        elif (state["tasks"][state["current_task"]]["status"] == "validated"
              or state["tasks"][state["current_task"]]["status"] == "new"):  # task is validated/new

            if state["tasks"][state["current_task"]]["status"] == "validated":
                state["current_task"] = get_new_task("Enum", state["tasks"])
                if state["current_task"] == -1:  # No more tasks for this agent
                    return {
                        "messages": [AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")]}

            task_str = state["tasks"][state["current_task"]]["task"]
            target_ip = state["tasks"][state["current_task"]]["target_ip"]
            state["tasks"][state["current_task"]]["status"] = "working"
            agent_messages.append(AIMessage(f"EnumAgent: Starting new task {state["current_task"]}: \"{task_str}\"."))

            if not state["tasks"][state["current_task"]]["preflightcheck"]:  # No PFC yet
                if state["tasks"][state["current_task"]]["target_ip"] in state["hosts"].keys():  # Target IP has entry in host table
                    agent_messages.append(AIMessage(f"EnumAgent: Sending task {state["current_task"]}: \"{task_str}\" to validator for pre-flight check."))
                    return{
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

        else:  # No tasks available, routing back to Stinger
            return {"messages": [AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")]}

    ## Setting up LLM Call
    if task_str is not None:

        enum_prompt_template = get_enum_prompt_template()
        enum_prompt = enum_prompt_template.invoke(
            {
                "tasks": task_str,
                "context": context
            }
        )

        response = llm_with_tools.invoke(enum_prompt)
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
        return {"messages": [AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def enum_router(state: StingerState):
    last_message = state["messages"][-1]
    current_task = state["tasks"][state["current_task"]]
    preflightcheck = current_task["preflightcheck"]

    if last_message.tool_calls: return "EnumToolNode"
    if not preflightcheck: return "EnumValidator"

    return "EnumHandoff"


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
        output = response.tool_calls[0]["args"]
        state["tasks"][state["current_task"]]["output"].append(output)

        return {
            "messages": state["messages"],
            "hosts": state["hosts"],
            "tasks": state["tasks"]
        }
    else:
        return {
            "messages": [AIMessage("EnumOutPutFormatter: No tool output, passing to EnumAgent.")]
        }


def validator(state: StingerState):
    state["tasks"][state["current_task"]]["preflightcheck"] = True
    target_ip = state["tasks"][state["current_task"]]["target_ip"]
    validator_prompt_template = get_task_answer_prompt_template()
    validator_prompt = validator_prompt_template.invoke(
        {
            "task": state["tasks"][state["current_task"]]["task"],
            "host_data": state["hosts"][target_ip]
        }
    )

    llm_with_structured_output = llm.with_structured_output(TaskAnswer)
    response = llm_with_structured_output.invoke(validator_prompt)

    if response.answer == "":  # Check if task needs further processing from blank answer
        return {
            "messages": [AIMessage("EnumValidator: Task unanswered, passing to EnumAgent.")]
        }
    else:
        state["tasks"][state["current_task"]]["status"] = "validated"
        state["tasks"][state["current_task"]]["answer"] = response

        return {
            "messages": [AIMessage(f"EnumValidator: Task {state["current_task"]} validated.\n"
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
enum_workflow = StateGraph(StingerState)

enum_workflow.add_edge(START, "EnumAgent")
enum_workflow.add_node("EnumAgent", enum_agent)

enum_workflow.add_conditional_edges("EnumAgent", enum_router, ["EnumToolNode", "EnumHandoff", "EnumValidator"])
enum_workflow.add_node("EnumToolNode", enum_tool_node)
enum_workflow.add_node("EnumHandoff", handoff)

enum_workflow.add_edge("EnumToolNode", "EnumOutputFormatter")
enum_workflow.add_node("EnumOutputFormatter", output_formatter)

enum_workflow.add_edge("EnumOutputFormatter", "HostUpdate")
enum_workflow.add_node("HostUpdate", host_update)

enum_workflow.add_edge("HostUpdate", "EnumValidator")
enum_workflow.add_node("EnumValidator", validator)

enum_workflow.add_edge("EnumValidator", "EnumAgent")

enum_graph = enum_workflow.compile()

if __name__ == "__main__":
    config = Configuration
    test_state = StingerState(
        tasks=[{"task": "Find common open ports on 127.0.0.1.",
                "status": "new",
                "agent": "Enum"}],
        hosts={},
        context="",
        messages=[HumanMessage("Find common open ports on 127.0.0.1")],
        next=""
    )

    enum_graph.invoke(test_state, {"recursion_limit": 6})
