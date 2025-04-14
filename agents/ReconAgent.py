from ipaddress import ip_address

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers
from utils.Prompts import get_recon_prompt_template, get_output_format_prompt_template
from utils.States import StingerState, Host, Port

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]
recon_tool_node = ToolNode(rb_tools)

def recon_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    tasks = state["tasks"]
    context = state["context"]
    task_call = None

    for index, task in enumerate(tasks):
        if task["agent"] == "Recon":
            if task["status"] == "new": # The task hasn't been executed
                task_call = task["task"]
                state["tasks"][index]["status"] = "working" # Mark task as executed
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
        return {
            "messages": [response],
            "tasks": state["tasks"]
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
            hostname= output["hostname"],
            ports= {}
        )

        for index, port in enumerate(output["ports"]):
            port_data = port.split('/') #splitting data e.g. 22/tcp
            target_host["ports"][port] = Port(
                    port= port_data[0],
                    protocol= port_data[1],
                    state= output["states"][index],
                    service= output["services"][index],
                    version=output["versions"][index],
                    scripts=output["scripts"][index]
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

# Defining the agent graph
recon_workflow = StateGraph(StingerState)

recon_workflow.add_edge(START, "ReconAgent")
recon_workflow.add_node("ReconAgent", recon_agent)

recon_workflow.add_conditional_edges("ReconAgent", recon_router, ["ReconToolNode", "ReconHandoff"])
recon_workflow.add_node("ReconToolNode", recon_tool_node)
recon_workflow.add_node("ReconHandoff", handoff)

recon_workflow.add_edge("ReconToolNode", "OutputFormatter")
recon_workflow.add_node("OutputFormatter", output_formatter)

recon_workflow.add_edge("OutputFormatter", "ReconAgent")

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
