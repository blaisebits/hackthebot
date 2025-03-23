from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.Prompts import get_recon_prompt_template
from utils.States import ReconState

from pprint import pprint

rb = RoboPages()
rb_tools = rb.get_tools()

#Node names for convenience
__ReconAgent = "ReconRouter"
__ReconToolNode = "ReconToolNode"


def recon_model_call(state: ReconState):
    llm = Configuration["llm"]
    llm_with_tools = llm.bind_tools(rb_tools)
    tasks = state["tasks"]
    context = state["context"]

    recon_prompt_template = get_recon_prompt_template()

    recon_prompt = recon_prompt_template.invoke(
        {
            "tools": rb_tools,
            "tasks": tasks,
            "context": context
        }
    )

    response = llm_with_tools.invoke(recon_prompt)
    return {"messages": [response]}


def recon_router(state: ReconState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return __ReconToolNode
    return END


recon_tool_node = ToolNode(rb_tools)

# Defining the agent graph
recon_workflow = StateGraph(ReconState)

recon_workflow.add_node(__ReconAgent, recon_model_call)
recon_workflow.add_node(__ReconToolNode, recon_tool_node)

recon_workflow.add_edge(START, __ReconAgent)
recon_workflow.add_conditional_edges(__ReconAgent, recon_router, [__ReconToolNode, END])
recon_workflow.add_edge(__ReconToolNode, __ReconAgent)

recon_graph = recon_workflow.compile()

if __name__ == "__main__":
    config = Configuration
    test_state = ReconState(
        tasks="Find common open ports on scanme.nmap.org.",
        hosts={},
        context="",
        messages=[]
    )

    recon_graph.invoke(test_state, {"recursion_limit": 3})
