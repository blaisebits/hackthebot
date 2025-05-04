from utils.HostUpdate import get_stub_host
from utils.States import Task, StingerState


def get_new_task(agent: str, tasks: [Task]) -> int:
    """Get the index to the first new task assigned to the agent"""
    for index, task in enumerate(tasks):
        if task["agent"] == agent and task["status"] == "new": return index

    return -1
