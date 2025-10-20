from typing import List

from utils.OutputFormatters import TaskBasicInfo
from utils.States import Task, StingerState, ExploitTask, ExploitStep


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
        step_task= step_task,
        status= "new",
        tool= [],
        output= []
    )

def get_current_exploit_task(state: StingerState) -> int:
    """
    Checks the state table for the currently working exploit task
    Returns -1 if no working task is found
    """
    for index, element in enumerate(state["tasks"][state["current_task"]]["output"]):
        if element["status"] == "working":
            return index

    return -1

##Output format helpers
def format_tool_output(tools:list[str], outputs:list[dict]) -> dict:
    """
    Takes in a list of tools and list of outputs and returns a single dictionary
    for inserting into LLM context.
    """
    print("***************************************************************************")
    print(tools)
    print(outputs)
    print("***************************************************************************")
    x = {}
    for i, tool in enumerate(tools):
        x["tool"] = outputs[i]

    return x

