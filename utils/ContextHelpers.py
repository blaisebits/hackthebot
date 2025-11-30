from typing import List

from utils.States import StingerState, ExploitTask, ExploitStep
from utils.Tasking import get_current_exploit_task_step, get_current_exploit_task


def build_exploit_task_context(state:StingerState) -> str:
    """
    Takes the state and the exploit task index
    returns a formatted string of all the steps' outputs
    """
    exploit_task_index:int = get_current_exploit_task(state)
    exploit_task: ExploitTask = state["tasks"][state["current_task"]]["output"][exploit_task_index]
    exploit_steps: List[ExploitStep] = exploit_task["steps"]
    current_step_index: int = get_current_exploit_task_step(state)

    context = "Previous Exploit steps:\n"
    for i in range(current_step_index+1):
        i_task = exploit_steps[i]["step_task"]
        i_scratchpad = exploit_steps[i]["scratchpad"]
        if len(i_scratchpad) != 0:
            context += f"* {i_task}:\n{i_scratchpad}\n\n"

    return context
