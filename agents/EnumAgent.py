from typing import Literal

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.constants import START
from langgraph.graph import add_messages, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers
from utils.Prompts import get_output_format_prompt_template
from utils.States import StingerState, Host, Port

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
enum_tool_node = ToolNode(rb_tools)

## STILL STUB CODE DUMBASS!
def enum_agent(state: StingerState):
    task_call = None

    for index, task in enumerate(state["tasks"]):
        if task["agent"] == "Enum":
            if task["status"] == "new": # The task hasn't been executed
                state["tasks"][index]["status"] = "working" # Mark task as executed
                # task_call = task["task"]
                # break # stopping at first 'new' task

    result = AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")

    return Command(
        goto="StingerAgent",
        update={
            "messages": result,
            "tasks": state["tasks"]
        },
        graph=Command.PARENT
    )

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
            hostname= output["hostname"],
            ports= {}
        )

        #commit host data to the state table
        state["hosts"][f"{target_host["hostname"]}({target_host["ip_address"]})"] = target_host

    return {
        "messages": state["messages"],
        "hosts": state["hosts"]
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

# enum_workflow.add_conditional_edges("EnumAgent", enum_router, ["EnumToolNode", "EnumHandoff"])
# enum_workflow.add_node("EnumToolNode", enum_tool_node)
# enum_workflow.add_node("EnumHandoff", handoff)
#
# enum_workflow.add_edge("EnumToolNode", "OutputFormatter")
# enum_workflow.add_node("OutputFormatter", output_formatter)

enum_graph = enum_workflow.compile()