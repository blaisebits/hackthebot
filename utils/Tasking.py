from langchain_core.messages import ToolMessage

from utils.OutputFormatters import TaskBasicInfo
from utils.States import Task, StingerState, ExploitTask, ExploitStep

def annoying_debug(x):
    print("="*70)
    print(x)
    print("="*70)

def get_new_task(agent: str, tasks: [Task]) -> int:
    """Get the index to the first new task assigned to the agent. Returns -1 on no task found."""
    for index, task in enumerate(tasks):
        if task["agent"] == agent and task["status"] == "new": return index

    return -1

def expand_task_basic_info(x: TaskBasicInfo) -> Task:
    return Task(
        task= x.task,
        preflightcheck= False,
        status="new",
        agent= x.agent,
        tool= [],
        output= [],
        target_ip= x.target_ip,
        verdict= None
    )

## Exploit helpers
def expand_exploit_suggestion(target_ip:str, task: str) -> ExploitTask:
    return ExploitTask(
        task= task,
        status= "new",
        verdict= None,
        current_step = 0,
        steps= [],
        target_ip= target_ip,
        initial_access_exploit=""
    )

def create_exploit_step(step_task: str)-> ExploitStep:
    """
    Takes in step task string and returns ExploitStep
    """
    return ExploitStep(
        iterations = 0,
        step_task= step_task,
        status= "new",
        scratchpad= ""
        # tool= [],
        # output= []
    )

def get_current_exploit_task(state: StingerState) -> int:
    """
    Checks the state table for the currently working exploit task
    Returns -1 if no working task is found
    """
    for index, task in enumerate(state["tasks"][state["current_task"]]["output"]):
        if task["status"] == "working":
            return index

    return -1

def get_current_exploit_task_step(state: StingerState) -> int:
    """
    Checks the state table for the currently working exploit step
    Returns -1 if no working task is found
    """
    current_exploit_task = get_current_exploit_task(state)
    # for task in state["tasks"][state["current_task"]]["output"]:
    #     if task["status"] == "working":
    # noinspection PyTypeChecker
    for index, step in enumerate(state["tasks"][state["current_task"]]["output"][current_exploit_task]["steps"]):
        if step["status"] == "working" or step["status"] == "new":
            return index


    return -1

##Output format helpers
def format_tool_output(tools:list[str], outputs:list[ToolMessage|str]) -> str:
    """
    Takes in a list of tools and list of outputs and returns a single dictionary
    for inserting into LLM context. Ignores tasks with empty output.
    """

    data:str = ""

    for index, tool in enumerate(tools):
        if len(outputs[index]) != 0:
            data += f"* {tool} => {outputs[index]}\n"

    return data

