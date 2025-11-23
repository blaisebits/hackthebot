from typing import List

from utils.States import StingerState, ExploitTask, ExploitStep

def build_exploit_task_context(state:StingerState, exploit_task_index:int) -> str:
    """
    Takes the state and the exploit task index
    returns a formatted string of all the steps' outputs
    """
    exploit_task: ExploitTask = state["tasks"][state["current_task"]]["output"][exploit_task_index]
    exploit_steps: List[ExploitStep] = exploit_task["steps"]
    current_step: int = exploit_task["current_step"]

    context = "Previous Exploit steps:\n"
    for i in range(current_step+1):
        i_task = exploit_steps[i]["step_task"]
        i_output = exploit_steps[i]["output"]
        if len(i_output) != 0:
            context += f"* {i_task}:\n{i_output}\n\n"

    return context
