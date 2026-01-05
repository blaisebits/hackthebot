from copy import deepcopy

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.HostUpdate import host_update, get_stub_host
from utils.LLMHelpers import llm_invoke_retry

from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_recon_prompt_template, get_output_format_prompt_template, get_task_answer_prompt_template
from utils.SpecialAgents import SpecialAgents
from utils.States import StingerState, Task, Host
from utils.Tasking import get_new_task, annoying_debug, get_working_task
from utils.Tooling import RoboPagesTools

rb = RoboPagesTools
rb_tools = rb.get_tools()

sp = SpecialAgents

llm = Configuration["llm"]
recon_tool_node = ToolNode(rb_tools)

def recon_agent(state: StingerState):
    """
    Primary Tasking Node
    **OUTPUT MAPPING**
        "messages"    : agent_messages,
        "tasks"       : output_task,
        "current_task": output_current_task,
        "hosts"       : output_hosts
    """
    llm_with_tools = llm.bind_tools(rb_tools)
    task_str:str = None
    agent_messages = []
    context = []
    input_current_task: int = state["current_task"]
    input_task: Task = state["tasks"][ input_current_task ]
    input_hosts: dict[str, Host] | Host | None = None
    output_current_task:int|None = None
    output_task:Task|None = None
    output_hosts:dict[str, Host]|None = None

    if (input_task["agent"] != "Recon" or
            (input_task["status"] not in ["working","new"])):
        return {"messages": [AIMessage("ReconAgent: Task not assigned to me. Passing to Stinger.")]}

    output_current_task = input_current_task
    input_task = state["tasks"][ input_current_task ]
    target_ip = input_task["target_ip"]
    input_hosts = state["hosts"][ target_ip ] if target_ip in state["hosts"].keys() else None

    output_task = deepcopy(state["tasks"][ input_current_task ])

    # Have a valid task to work with at this point
    if input_task["status"] == "new":
        task_str = input_task["task"]
        target_ip = input_task["target_ip"]
        output_task = deepcopy(state["tasks"][output_current_task])
        # annoying_debug(output_task)
        output_task["status"] = "working"
        annoying_debug(state["tasks"][output_current_task])
        agent_messages.append(AIMessage(f"ReconAgent: Starting new task {output_current_task}: \"{task_str}\"."))

        # Preflight check is false
        if not input_task["preflightcheck"]:
            # Host is already being tracked
            if input_hosts is not None:
                # Target IP has entry in host table
                agent_messages.append(AIMessage(
                    f"ReconAgent: Sending task {output_current_task}: \"{task_str}\" to validator for pre-flight check."))
                return {
                    "messages": agent_messages,
                    "current_task": output_current_task
                }
            else:
                # Add blank entry to host table
                target_ip = state["tasks"][output_current_task]["target_ip"]
                target_host = get_stub_host(target_ip)
                target_host["preflightcheck"] = True
                output_hosts = { target_host["ip_address"]: target_host }
                task_str = input_task["task"]

        context.append(output_hosts[target_ip])

    # Task status is "working"
    else:
        task_str = input_task["task"]
        target_ip = input_task["target_ip"]
        context.append(input_hosts[target_ip])
        agent_messages.append(AIMessage(f"ReconAgent: Reworking task {output_current_task}: \"{task_str}\"."))

    ## Setting up LLM Call
    if task_str is not None:

        recon_prompt_template = get_recon_prompt_template()
        recon_prompt = recon_prompt_template.invoke(
            {
                "tasks": task_str,
                "context": context
            }
        )

        # response = llm_with_tools.invoke(recon_prompt)
        response = llm_invoke_retry(llm_with_tools, recon_prompt)
        output_task["tool"].append(response.tool_calls[0]["name"])
        agent_messages.append(response)
        return {
            "messages": agent_messages,
            "tasks": output_task,
            "current_task": output_current_task,
            "hosts": output_hosts
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
    """
    Output Formatting Node
    
    **OUTPUT MAPPING**
        "messages": output_messages
        "tasks"   : output_task
        "hosts"   : output_host #not in use
    """

    second_last_message:AIMessage = state["messages"][-2]
    last_message: ToolMessage = state["messages"][-1]
    output_messages: list[AnyMessage] = []
    output_task: Task | None = None
    # output_host: dict[str, Host] | None = None

    if last_message.type == 'tool':
        llm_output_format_selection = llm.bind_tools(tool_parsers)
        tool_intput = second_last_message.tool_calls
        tool_output = last_message.content

        output_format_prompt_template = get_output_format_prompt_template()
        output_format_prompt = output_format_prompt_template.invoke(
            {
                "tool_input": tool_intput,
                "tool_output": tool_output
            }
        )

        response = llm_invoke_retry(llm_output_format_selection,output_format_prompt)
        output_messages.append(response)
        output  = response.tool_calls[0]["args"]
        output_task = deepcopy(state["tasks"][ state["current_task"] ])
        output_task["output"].append(output)

        return {
            "messages": output_messages,
            # "hosts": state["hosts"],
            "tasks": output_task
        }
    else:
        return {
            "messages": [AIMessage("ReconOutPutFormatter: No tool output, passing to ReconAgent.")]
        }


def validator(state: StingerState):
    """
    Output Formatting Node

    **OUTPUT MAPPING**
        "messages": output_messages
        "tasks"   : output_task
        "hosts"   : output_host 
    """
    output_messages: list[AnyMessage] = []
    output_task: Task = deepcopy(state["tasks"][ state["current_task"] ])
    output_host: Host | None = None

    output_task["preflightcheck"] = True
    target_ip = output_task["target_ip"]
    output_host = deepcopy(state["hosts"][ target_ip ])
    validator_prompt_template = get_task_answer_prompt_template()
    validator_prompt = validator_prompt_template.invoke(
        {
            "task": output_task["task"],
            "host_data": output_host
        }
    )

    llm_with_structured_output = llm.with_structured_output(TaskAnswer)
    response = llm_invoke_retry(llm_with_structured_output,validator_prompt)

    if response.answer == "":    # Check if task needs further processing from blank answer
        return {
            "messages": [AIMessage("ReconValidator: Task unanswered, passing to ReconAgent.")]
        }
    else:
        # noinspection PyTypedDict
        output_task["status"] = "validated"
        output_task["verdict"] = response

        output_host["verdicts"].append(response)

        return {
            "messages": [AIMessage(f"ReconValidator: Task {state["current_task"]} validated.\n"
                                   f"Question: {response.question}\n"
                                   f"Answer: {response.answer}\n")],
            "tasks": output_task,
            "hosts": {target_ip: output_host}
        }


def handoff(state: StingerState):
    """Hand off back to stinger"""
    return Command(
        goto="StingerAgent",
        update=state,
        graph=Command.PARENT
    )

# Defining the agent graph
# noinspection PyTypeChecker
recon_workflow = StateGraph(StingerState)

recon_workflow.add_edge(START, "ReconAgent")
# noinspection PyTypeChecker
recon_workflow.add_node("ReconAgent", recon_agent)

recon_workflow.add_conditional_edges("ReconAgent", recon_router, ["ReconToolNode", "ReconHandoff", "ReconValidator"])
recon_workflow.add_node("ReconToolNode", recon_tool_node)
# noinspection PyTypeChecker
recon_workflow.add_node("ReconHandoff", handoff)

recon_workflow.add_edge("ReconToolNode", "ReconOutputFormatter")
# noinspection PyTypeChecker
recon_workflow.add_node("ReconOutputFormatter", output_formatter)

recon_workflow.add_edge("ReconOutputFormatter", "HostUpdate")
# noinspection PyTypeChecker
recon_workflow.add_node("HostUpdate", host_update)

recon_workflow.add_edge("HostUpdate", "ReconValidator")
# noinspection PyTypeChecker
recon_workflow.add_node("ReconValidator", validator)

recon_workflow.add_edge("ReconValidator", "ReconAgent")

recon_graph = recon_workflow.compile()
