from utils.HostUpdate import get_stub_host
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

def expand_exploit_suggestion(target_ip:str, task: str) -> ExploitTask:
    return ExploitTask(
        task= task,
        status= "new",
        verdict= None,
        current_step = 0,
        steps= [],
        target_ip= target_ip
    )

def get_exploit_step(step_task: str)-> ExploitStep:
    return ExploitStep(
        step_task= step_task,
        status= "new",
        tool= [],
        output= []
    )