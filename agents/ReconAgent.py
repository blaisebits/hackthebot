from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import tool_parsers
from utils.Prompts import get_recon_prompt_template, get_output_format_prompt_template
from utils.States import StingerState

rb = RoboPages()
rb_tools = rb.get_tools()
llm = Configuration["llm"]

def recon_agent(state: StingerState):
    llm_with_tools = llm.bind_tools(rb_tools)
    tasks = state["tasks"]
    context = state["context"]
    task_call = None

    for task in tasks:
        if task["status"] == "new": # The task hasn't been executed
            task_call = task["task"]
            task["status"] = "working" # Mark task as executed
            break

    if task_call is not None:
        recon_prompt_template = get_recon_prompt_template()
        recon_prompt = recon_prompt_template.invoke(
            {
                "tasks": task_call,
                "context": context
            }
        )

        response = llm_with_tools.invoke(recon_prompt)
        return {"messages": [response]}
    else:
        # return no tasks response
        return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution. Passing to Stinger.")]}


def recon_router(state: StingerState):
    last_message = state["messages"][-1]

    if last_message.type == 'ai' and last_message.tool_calls:
        return "ReconToolNode"
    return END

recon_tool_node = ToolNode(rb_tools)

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

        # if last_message.type == 'ai' and last_message.tool_calls:
        #     parser_name = response.tool_calls["name"]
        #     parser = None
        #     for tool in tool_parsers:
        #         if tool.__name__ == parser_name: parser = tool
        #
        #     if parser is not None:
        #         llm_output_formatter = llm.with_structured_output(parser)
        #         output_format_prompt = output_format_prompt_template.invoke(
        #             {
        #                 "tool_output": tool_output
        #             }
        #         )
        #         response = llm_output_formatter.invoke(output_format_prompt)
        #         state["messages"] = add_messages(state["messages"], response)
        #         state["context"] = response.tool_calls

    return {
        "messages": state["messages"],
        "context": state["context"]
    }

# Defining the agent graph
recon_workflow = StateGraph(StingerState)

recon_workflow.add_edge(START, "ReconAgent")
recon_workflow.add_node("ReconAgent", recon_agent)
recon_workflow.add_conditional_edges("ReconAgent", recon_router, ["ReconToolNode", END])
recon_workflow.add_node("ReconToolNode", recon_tool_node)
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
#       "content": "Find common open ports on scanme.nmap.org.",
#       "type": "human"
#     }
#   ]
# }
