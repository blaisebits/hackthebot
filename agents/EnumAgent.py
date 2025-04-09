from typing import Literal

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.constants import START
from langgraph.graph import add_messages, StateGraph
from langgraph.types import Command

from utils.States import StingerState

def enum_agent(state: StingerState):
    result = AIMessage("Passing from EnumAgent stub.")
    tasks = state["tasks"]
    completed_tasks_list = []

    for task in tasks:
        if task["agent"] == "Enum":
            task.status = "completed"
            completed_tasks_list.append(task)


    return {
        "messages": result,
        "tasks": completed_tasks_list
    }

enum_workflow = StateGraph(StingerState)

enum_workflow.add_edge(START, "Enum")
enum_workflow.add_node("Enum", enum_agent)