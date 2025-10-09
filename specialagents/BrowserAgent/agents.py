from langchain_core.messages import AIMessage
from langgraph.constants import START
from langgraph.graph import StateGraph
from specialagents.BrowserAgent.Browser import PersistentBrowserAgent
from utils.ContextHelpers import build_exploit_task_context
from utils.States import StingerState, ExploitTask, Task, ExploitStep
from utils.Tasking import get_current_exploit_task

_AGENT_NAME="BrowserAgent"
_AGENT_MAPPING=["Recon","Enum","Exploit"]
_AGENT_DESCRIPTION="Provides access to a fully functional web browser, handling task such as browsing, navigating, uploading or downloading files."

def output_format(result, agent_messages):
    output: str = f"{_AGENT_NAME}:\n"
    for m in result["messages"]:
        if m.type == "human" or m.type == "tool":
            output += f"{m.content}\n"
            agent_messages.append(m)
        elif m.type == "ai":  # dirty check for AI content structure
            if isinstance(m.content, str):
                output += f"{m.content}\n"
                agent_messages.append(m)
            elif isinstance(m.content, list):
                if isinstance(m.content[0], str):
                    output += f"{m.content[0]}\n"
                    agent_messages.append(m)
                elif isinstance(m.content[0], dict):
                    output += f"{m.content[0]["text"]}\n"
                    agent_messages.append(m)
        else:
            agent_messages.append(m)  # catch all
    return output, agent_messages

async def browser_wrapper(state: StingerState):
    agent:PersistentBrowserAgent = None
    agent_messages:list = []
    result:list = None

    # Check for existing browser or create one
    current_task = state["current_task"]
    target_ip = state["tasks"][current_task]["target_ip"]
    session_name = f"browser_{target_ip}"
    if _AGENT_NAME in state["persistent_tools"]:
        if session_name in state["persistent_tools"][_AGENT_NAME]:
            agent = state["persistent_tools"][_AGENT_NAME][session_name]
        else:
            agent = PersistentBrowserAgent(session_name)
            state["persistent_tools"][_AGENT_NAME] = { session_name: agent }
    else:
        agent = PersistentBrowserAgent(session_name)
        state["persistent_tools"][_AGENT_NAME] = { session_name: agent }
    agent_messages.append(AIMessage(f"{_AGENT_NAME}: Using browser session '{session_name}"))

    # Extract task from EXPLOIT tasks
    if state["tasks"][state["current_task"]]["agent"] == "Exploit":
        ## DO EXPLOIT (agent) STUFF
        task:Task = state["tasks"][state["current_task"]]
        task_output:ExploitTask = task["output"][0] # TODO Fix to properly target ExploitTask, not [0]
        step_index:int = task_output["current_step"]
        # step:ExploitStep = task_output["steps"][step_index]
        step_task = task_output["steps"][step_index]["step_task"]

        ## create a context for the task
        exploit_task_index: int = get_current_exploit_task(state)
        browser_task = f"{step_task}\n{build_exploit_task_context(state, exploit_task_index)}"
        result = await agent.execute_task(browser_task)
        state["tasks"][current_task]["output"][0]["steps"][step_index]["tool"] += [_AGENT_NAME]
        ### TODO Need output logic moved from line 59 here
        output, agent_messages = output_format(result, agent_messages)
        state["tasks"][current_task]["output"][0]["steps"][step_index]["output"] += [result]

    #extract tasks for all other agents
    else:
        task_obj: Task = state["tasks"][state["current_task"]]
        task: str = task_obj["task"]

        result = await agent.execute_task(task)
        state["tasks"][current_task]["tool"] += [_AGENT_NAME]
        output, agent_messages = output_format(result, agent_messages)
        state["tasks"][current_task]["output"] += [output]
    # agent_messages.append(result["messages"])

    # pick = {
    #     "BrowserAgentResult": result,
    #     "AgentMessages": agent_messages
    # }
    # with open('output.pickle', 'wb') as file:
    #     pickle.dump(pick, file)


    return {
        "messages": agent_messages,
        "persistent_tools": state["persistent_tools"],
        "tasks": state["tasks"]
    }

browser_agent_workflow = StateGraph(StingerState)

browser_agent_workflow.add_edge(START, "Browser")
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