from copy import deepcopy

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.HostUpdate import host_update, get_stub_host
from utils.LLMHelpers import llm_invoke_retry

from utils.OutputFormatters import tool_parsers, TaskAnswer
from utils.Prompts import get_enum_prompt_template, get_output_format_prompt_template, get_task_answer_prompt_template
from utils.SpecialAgents import SpecialAgents
from utils.States import StingerState, Task, Host
from utils.Tasking import annoying_debug
from utils.Tooling import RoboPagesTools

rb = RoboPagesTools
rb_tools = rb.get_tools()

sp = SpecialAgents

llm = Configuration["llm"]
enum_tool_node = ToolNode(rb_tools)


def enum_agent(state: StingerState):
    """
    Primary Tasking Node
    **OUTPUT MAPPING**
        "messages"    : agent_messages,
        "tasks"       : output_task,
        "current_task": output_current_task,
        "hosts"       : output_hosts
    """
    llm_with_tools = llm.bind_tools(rb_tools)
    task_str: str|None = None
    agent_messages = []
    context = []
    input_current_task: int = state["current_task"]
    input_task: Task = state["tasks"][input_current_task]
    input_hosts: dict[str, Host] | Host | None = None
    output_current_task: int | None = None
    output_task: Task | None = None

    if (input_task["agent"] != "Enum" or
            (input_task["status"] not in ["working", "new"])):
        return {"messages": [AIMessage("EnumAgent: Task not assigned to me. Passing to Stinger.")]}

    output_current_task = input_current_task
    input_task = state["tasks"][input_current_task]
    target_ip = input_task["target_ip"]
    input_hosts = state["hosts"] if target_ip in state["hosts"].keys() else None
    output_hosts: dict[str, Host] | None = None

    output_task = deepcopy(state["tasks"][input_current_task])

    # Working on a task with a "new" status
    if input_task["status"] == "new":
        task_str = input_task["task"]
        output_task = deepcopy(state["tasks"][output_current_task])
        # annoying_debug(output_task)
        output_task["status"] = "working"
        annoying_debug(state["tasks"][output_current_task])
        agent_messages.append(AIMessage(f"EnumAgent: Starting new task {output_current_task}: \"{task_str}\"."))

        # Preflight check is false
        if not input_task["preflightcheck"]:
            # Host is already being tracked
            if input_hosts is not None:
                # Target IP has entry in host table
                agent_messages.append(AIMessage(
                    f"EnumAgent: Sending task {output_current_task}: \"{task_str}\" to validator for pre-flight check."))
                return {
                    "messages": agent_messages,
                    "current_task": output_current_task
                }
            else:
                # Add blank entry to host table
                target_host = get_stub_host(target_ip)
                target_host["preflightcheck"] = True
                input_hosts = {target_host["ip_address"]: target_host}
                task_str = input_task["task"]

    # Working on a task with a "working" status
    else:
        task_str = input_task["task"]
        agent_messages.append(AIMessage(f"EnumAgent: Reworking task {output_current_task}: \"{task_str}\"."))


    ## Setting up LLM Call
    if task_str is not None:
        context.append(input_hosts[target_ip])
        output_hosts = deepcopy(input_hosts)
        enum_prompt_template = get_enum_prompt_template()
        enum_prompt = enum_prompt_template.invoke(
            {
                "tasks": task_str,
                "context": context,
                "previous_attempts": input_task["output"]
            }
        )

        # response = llm_with_tools.invoke(enum_prompt)
        response = llm_invoke_retry(llm_with_tools, enum_prompt)
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
        return {"messages": [AIMessage("EnumAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def enum_router(state: StingerState):
    last_message = state["messages"][-1]
    current_task = state["tasks"][state["current_task"]]
    preflightcheck = current_task["preflightcheck"]

    if last_message.tool_calls: return "EnumToolNode"
    if not preflightcheck: return "EnumValidator"

    return "EnumHandoff"


def output_formatter(state: StingerState):
    """
    Output Formatting Node

    **OUTPUT MAPPING**
        "messages": output_messages
        "tasks"   : output_task
        "hosts"   : output_host #not in use
    """

    second_last_message: AIMessage = state["messages"][-2]
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

        response = llm_invoke_retry(llm_output_format_selection, output_format_prompt)
        output_messages.append(response)
        output = response.tool_calls[0]["args"]
        output_task = deepcopy(state["tasks"][state["current_task"]])
        output_task["output"].append(output)

        return {
            "messages": output_messages,
            # "hosts": state["hosts"],
            "tasks": output_task
        }
    else:
        return {
            "messages": [AIMessage("EnumOutPutFormatter: No tool output, passing to EnumAgent.")]
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
    output_task: Task = deepcopy(state["tasks"][state["current_task"]])
    target_ip = output_task["target_ip"]
    output_hosts: dict[str, Host] = { target_ip: deepcopy(state["hosts"][target_ip]) }

    output_task["preflightcheck"] = True
    validator_prompt_template = get_task_answer_prompt_template()
    validator_prompt = validator_prompt_template.invoke(
        {
            "task": output_task["task"],
            "host_data": output_hosts[target_ip]
        }
    )

    llm_with_structured_output = llm.with_structured_output(TaskAnswer)
    response = llm_invoke_retry(llm_with_structured_output, validator_prompt)

    # Check if task needs further processing from blank answer
    if response.answer == "":
        return {
            "messages": [AIMessage("EnumValidator: Task unanswered, passing to EnumAgent.")],
            "tasks": output_task
        }
    else:
        # noinspection PyTypedDict
        output_task["status"] = "validated"
        output_task["verdict"] = response

        output_hosts[target_ip]["verdicts"].append(response)

        return {
            "messages": [AIMessage(f"EnumValidator: Task {state["current_task"]} validated.\n"
                                   f"Question: {response.question}\n"
                                   f"Answer: {response.answer}\n")],
            "tasks": output_task,
            "hosts": output_hosts
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
enum_workflow = StateGraph(StingerState)

enum_workflow.add_edge(START, "EnumAgent")
# noinspection PyTypeChecker
enum_workflow.add_node("EnumAgent", enum_agent)

enum_workflow.add_conditional_edges("EnumAgent", enum_router, ["EnumToolNode", "EnumHandoff", "EnumValidator"])
enum_workflow.add_node("EnumToolNode", enum_tool_node)
# noinspection PyTypeChecker
enum_workflow.add_node("EnumHandoff", handoff)

enum_workflow.add_edge("EnumToolNode", "EnumOutputFormatter")
# noinspection PyTypeChecker
enum_workflow.add_node("EnumOutputFormatter", output_formatter)

enum_workflow.add_edge("EnumOutputFormatter", "HostUpdate")
# noinspection PyTypeChecker
enum_workflow.add_node("HostUpdate", host_update)

enum_workflow.add_edge("HostUpdate", "EnumValidator")
# noinspection PyTypeChecker
enum_workflow.add_node("EnumValidator", validator)

enum_workflow.add_edge("EnumValidator", "EnumAgent")

enum_graph = enum_workflow.compile()
