from copy import deepcopy

from langchain_core.messages import AIMessage
from langgraph.constants import START
from langgraph.graph import StateGraph
from specialagents.BrowserAgent.Browser import PersistentBrowserAgent
from utils.ContextHelpers import build_exploit_task_context
from utils.States import StingerState, ExploitTask, Task
from utils.Tasking import get_current_exploit_task, get_current_exploit_step

_AGENT_NAME="BrowserAgent"
_AGENT_MAPPING=["Recon","Enum","Exploit"]
_AGENT_DESCRIPTION="Provides access to a fully functional web browser, handling task such as browsing, navigating, uploading or downloading files."

async def browser_wrapper(state: StingerState):
    agent:PersistentBrowserAgent|None = None
    agent_messages:list = []
    result:list|None = None
    input_persistent_tools:dict = state["persistent_tools"]
    input_tasks:list[Task] = state["tasks"]
    output_tasks:list[Task] = deepcopy(state["tasks"])
    output_persistent_tools:dict = {}

    # Check for existing browser or create one
    current_task = state["current_task"]
    target_ip = input_tasks[current_task]["target_ip"]
    session_name = f"browser_{target_ip}"
    if _AGENT_NAME in input_persistent_tools:
        if session_name in input_persistent_tools[_AGENT_NAME]:
            agent = input_persistent_tools[_AGENT_NAME][session_name]
        else:
            agent = PersistentBrowserAgent(session_name)
            output_persistent_tools[_AGENT_NAME] = { session_name: agent }
    else:
        agent = PersistentBrowserAgent(session_name)
        output_persistent_tools[_AGENT_NAME] = { session_name: agent }
    agent_messages.append(AIMessage(f"{_AGENT_NAME}: Using browser session '{session_name}"))

    task:Task = input_tasks[state["current_task"]]

    # Extract task from EXPLOIT tasks
    if task["agent"] == "Exploit":
        ## DO EXPLOIT (agent) STUFF
        current_exploit_task:int = get_current_exploit_task(state)
        task_output:ExploitTask = task["output"][current_exploit_task]
        step_index:int = get_current_exploit_step(state)

        # step:ExploitStep = task_output["steps"][step_index]
        step_task = task_output["steps"][step_index]["step_task"]

        ## create a context for the task
        exploit_task_index: int = get_current_exploit_task(state)
        browser_task = f"<TASK>\n{step_task}\n</TASK>\n<CONTEXT>\n{build_exploit_task_context(state)}</CONTEXT>"
        result = await agent.execute_task(browser_task)
        # noinspection PyTypeChecker
        output_tasks[current_task]["output"][current_exploit_task]["steps"][step_index]["scratchpad"] += result["messages"][-1].text()

    #extract tasks for all other agents
    else:
        task_obj: Task = input_tasks[state["current_task"]]
        task: str = task_obj["task"]

        result = await agent.execute_task(task)
        # noinspection PyTypeChecker
        output_tasks[current_task]["output"] += [result["messages"][-1].text()]

    return {
        "messages": agent_messages,
        "persistent_tools": output_persistent_tools,
        "tasks": output_tasks[current_task]
    }


# noinspection PyTypeChecker
browser_agent_workflow = StateGraph(StingerState)

browser_agent_workflow.add_edge(START, "Browser")
# noinspection PyTypeChecker
browser_agent_workflow.add_node("Browser", browser_wrapper)

browser_agent_graph = browser_agent_workflow.compile()

AGENT_MAPPING ={
    _AGENT_NAME: {
        "graph": browser_agent_graph,
        "agent_mapping":_AGENT_MAPPING,
        "description": _AGENT_DESCRIPTION
    }
}

# async def main():
#     tasks = [
#         "Browse to http://10.201.123.113/panel and upload /data/web-shells/Dysco.php"
#     ]
#     print("--- Upload Test ---")
#     agent1 = PersistentBrowserAgent("test_session")
#     result1 = await agent1.execute_task(tasks[0])
#     print(f"Upload Test: ✓")
#     print(f"Results: {result1["messages"]}")
#     await agent1.close_browser_session()

# if __name__ == "__main__":
#     asyncio.run(main())