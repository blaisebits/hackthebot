from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.constants import START
from langgraph.graph import add_messages, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_output_format_prompt_template, get_enum_prompt_template, get_task_answer_prompt_template
from utils.States import StingerState, Host

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
enum_tool_node = ToolNode(rb_tools)

def enum_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    context = ""
    task_call = None
    agent_messages = []

    current_task = state["tasks"][state["current_task"]]
    is_new_task = current_task["status"] == "new"
    is_working_task = current_task["status"] == "working"
    is_validated_task = current_task["status"] == "validated"
    is_assigned_enum = current_task["agent"] = "Enum"

    ## Check the CURRENT TASK status and take action
    if is_assigned_enum and not is_validated_task:
        task_call = current_task["task"]
        if is_working_task:
            context = [
                state["context"],
                current_task["output"]
            ]
            agent_messages.append(AIMessage(f"EnumAgent: Reworking task {state["current_task"]}: \"{task_call}\"."))
        if is_new_task:
            state["tasks"][state["current_task"]]["status"] = "working"
            context = state["context"]
            agent_messages.append(AIMessage(f"EnumAgent: Starting new task {state["current_task"]}: \"{task_call}\"."))
    else:
        for index, task in enumerate(state["tasks"]):  # Find the first 'new' task
            if task["agent"] == "Enum":
                if task["status"] == "new":  # The task hasn't been executed
                    task_call = task["task"]
                    state["tasks"][index]["status"] = "working"  # Mark task as executing
                    state["current_task"] = index
                    context = state["context"]
                    agent_messages.append(
                        AIMessage(f"EnumAgent: Starting new task {state["current_task"]}: \"{task_call}\"."))
                    break  # stopping at first 'new' task

    if task_call is not None:
        enum_prompt_template = get_enum_prompt_template()
        enum_prompt = enum_prompt_template.invoke(
            {
                "tasks": task_call,
                "context": context
            }
        )

        response = llm_with_tools.invoke(enum_prompt)
        state["tasks"][state["current_task"]]["tool"].append(response.tool_calls[0]["name"])
        agent_messages.append(response)

        return {
            "messages": agent_messages,
            "tasks": state["tasks"],
            "current_task": state["current_task"]
        }
    else:
        # return no tasks response
        return {"messages": [AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def enum_router(state: StingerState):
    last_message = state["messages"][-1]

    if last_message.type == 'ai' and last_message.tool_calls:
        return "EnumToolNode"
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
        output  = response.tool_calls[0]["args"]

        target_host = Host(
            ip_address= output["ip_address"],
            hostname= [output["hostname"]],
            ports= {}
        )

        #commit host data to the state table
        state["hosts"][f"{target_host["hostname"]}({target_host["ip_address"]})"] = target_host
        state["tasks"][state["current_task"]]["output"].append(output)
        state["tasks"][state["current_task"]]["status"] = "completed"

    return {
        "messages": state["messages"],
        "hosts": state["hosts"],
        "tasks": state["tasks"]
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

enum_workflow = StateGraph(StingerState)

enum_workflow.add_edge(START, "EnumAgent")
enum_workflow.add_node("EnumAgent", enum_agent)

enum_workflow.add_conditional_edges("EnumAgent", enum_router, ["EnumToolNode", "EnumHandoff"])
enum_workflow.add_node("EnumToolNode", enum_tool_node)
enum_workflow.add_node("EnumHandoff", handoff)

enum_workflow.add_edge("EnumToolNode", "EnumOutputFormatter")
enum_workflow.add_node("EnumOutputFormatter", output_formatter)

enum_workflow.add_edge("EnumOutputFormatter", "EnumValidator")
enum_workflow.add_node("EnumValidator", validator)

enum_workflow.add_edge("EnumValidator", "EnumAgent")

enum_graph = enum_workflow.compile()