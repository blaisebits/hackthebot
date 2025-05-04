from langchain_core.messages import AIMessage
from langgraph.constants import START
from langgraph.graph import add_messages, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from utils.Configuration import Configuration
from utils.HostUpdate import host_update
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
    context = state["context"]
    task_str = None
    agent_messages = []

    current_task = state["tasks"][state["current_task"]]
    is_new_task = current_task["status"] == "new"
    is_working_task = current_task["status"] == "working"
    is_validated_task = current_task["status"] == "validated"
    is_assigned_enum = current_task["agent"] = "Enum"
    preflightcheck = current_task["preflightcheck"]

    # Check if we can answer the task before calling tools
    if not preflightcheck:
        if current_task["target_ip"] in state["hosts"].keys():
            return {
                "messages": [AIMessage(f"EnumAgent: Sending task {state["current_task"]}: \"{task_str}\" to validator for pre-flight check.")]
            }
        else:
            state["tasks"][state["current_task"]]["preflightcheck"] = True

    ## Check the CURRENT TASK status and take action
    if is_assigned_enum and not is_validated_task:
        task_str = current_task["task"]
        if is_working_task:
            agent_messages.append(AIMessage(f"EnumAgent: Reworking task {state["current_task"]}: \"{task_str}\"."))
        if is_new_task:
            state["tasks"][state["current_task"]]["status"] = "working"
            agent_messages.append(AIMessage(f"EnumAgent: Starting new task {state["current_task"]}: \"{task_str}\"."))
    else:
        for index, task in enumerate(state["tasks"]):  # Find the first 'new' task
            if task["agent"] == "Enum":
                if task["status"] == "new":  # The task hasn't been executed
                    task_str = task["task"]
                    state["tasks"][index]["status"] = "working"  # Mark task as executing
                    state["current_task"] = index
                    agent_messages.append(
                        AIMessage(f"EnumAgent: Starting new task {state["current_task"]}: \"{task_str}\"."))
                    break  # stopping at first 'new' task

    # Setting up LLM call
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
            "current_task": state["current_task"]
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
        output  = response.tool_calls[0]["args"]

        target_host = Host(
            ip_address= output["ip_address"],
            hostname= [output["hostname"]],
            ports= {}
        )

        #commit host data to the state table
        state["hosts"][target_host["ip_address"]] = target_host
        state["tasks"][state["current_task"]]["output"].append(output)

    return {
        "messages": state["messages"],
        "hosts": state["hosts"],
        "tasks": state["tasks"]
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
            "messages": [AIMessage("EnumValidator: Task unanswered, passing to EnumAgent.")]
        }
    else:
        state["tasks"][ state["current_task"] ]["status"] = "validated"
        state["tasks"][ state["current_task"] ]["answer"] = response

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