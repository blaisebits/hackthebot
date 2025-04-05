from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from utils.Configuration import Configuration
from utils.LangChain_RoboPages import RoboPages
from utils.Prompts import get_recon_prompt_template
from utils.Logging import print_agent_message
from utils.States import ReconState

rb = RoboPages()
rb_tools = rb.get_tools()

#Node names for convenience
__ReconAgent = "ReconAgent"
__ReconToolNode = "ReconToolNode"


def recon_agent(state: ReconState):
    llm = Configuration["llm"]
    llm_with_tools = llm.bind_tools(rb_tools)
    tasks = state["tasks"]
    context = state["context"]
    task_call = None

    for task in tasks:
        #Check if true/false but as string and convert to bool
        if isinstance(task["completed"], str):
            if task["completed"].lower() == "true":
                task["completed"] = True
            else:
                task["completed"] = False

        if not task["completed"]: # The task hasn't been executed
            task_call = task["task"]
            task["completed"] = True # Mark task as executed
            break

    if task_call is not None:
        recon_prompt_template = get_recon_prompt_template()
        recon_prompt = recon_prompt_template.invoke(
            {
                "tools": rb_tools,
                "tasks": task_call,
                "context": context
            }
        )

        response = llm_with_tools.invoke(recon_prompt)
        return {"messages": [response]}
    else:
        # return no tasks response
        return {"messages": [AIMessage("ReconAgent: No Tasks were marked for execution.")]}


def recon_router(state: ReconState):
    last_message = state["messages"][-1]
    print_agent_message(last_message, log=True)

    if last_message.type == 'ai' and last_message.tool_calls:
        return __ReconToolNode
    return END


recon_tool_node = ToolNode(rb_tools)

# Defining the agent graph
recon_workflow = StateGraph(ReconState)

recon_workflow.add_node(__ReconAgent, recon_agent)
recon_workflow.add_node(__ReconToolNode, recon_tool_node)

recon_workflow.add_edge(START, __ReconAgent)
recon_workflow.add_conditional_edges(__ReconAgent, recon_router, [__ReconToolNode, END])
recon_workflow.add_edge(__ReconToolNode, __ReconAgent)

recon_graph = recon_workflow.compile()

if __name__ == "__main__":
    config = Configuration
    test_state = ReconState(
        tasks=[{"task":"Find common open ports on scanme.nmap.org.",
             "completed":False}],
        hosts={},
        context="",
        messages=[]
    )

    recon_graph.invoke(test_state, {"recursion_limit": 6})

# {
#   "tasks": [{"task":"Find common open ports on scanme.nmap.org.","completed":"False"}],
#   "hosts": {
#     "a": "b"
#   },
#   "context": "N/A",
#   "messages": [
#     {
#       "content": "Find common open ports on scanme.nmap.org.",
#       "type": "human"
#     }
#   ]
# }
