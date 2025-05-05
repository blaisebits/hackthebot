from typing import Literal

from langchain_core.messages import HumanMessage, AIMessage

from langgraph.graph import START, END, add_messages, StateGraph
from langgraph.types import Command

from agents.EnumAgent import enum_graph
from agents.ReconAgent import recon_graph
from utils.Configuration import Configuration
from utils.Prompts import get_tasklist_prompt_template
from utils.States import StingerState, TaskList

agents = ["Recon",
          "Enum",
          # "Exploit",
          # "PostEx"
          ]

llm = Configuration["llm"]

def user_input(state: StingerState):
    # stub code, will implement later

    if len(state["messages"]) == 0:
        human_message = HumanMessage(
            "* Find common open ports on 127.0.0.1."
        )
        return { "messages": human_message }
    else:
        return state


"""Called after User input to format initial task list"""
def initializer(state: StingerState):
    raw_tasks = state["messages"][-1].content
    #Ad Hoc fix for initializing the first tasks from UserInput
    stinger_context = state["context"] + "\n The `output`, `tool`, and `answer` parameters should be blank, and the `preflightcheck` should be false."

    tasklist_prompt_template = get_tasklist_prompt_template()
    tasklist_prompt = tasklist_prompt_template.invoke(
        {
            "tasks": raw_tasks,
            "members": agents,
            "context": stinger_context
        }
    )
    llm_with_structured_output = llm.with_structured_output(TaskList)
    response = llm_with_structured_output.invoke(tasklist_prompt)

    # Checking for and ordering task list by agent: Recon -> Enum -> Exploit -> PostEx
    ordered_task_list = []
    for task in response["tasks"]:
        for agent in agents:
            if task["agent"] == agent:
                ordered_task_list.append(task)
    return {
        "tasks": ordered_task_list
    }


def stinger_agent(state: StingerState) -> Command[Literal["Recon","Enum"]]:
    goto = ""
    agent_message = ""
    for index, task in enumerate(state["tasks"]):
        if task["status"] == "new":
            goto = task["agent"]
            state["current_task"] = index
            agent_message = [AIMessage(f"StingerAgent: Passing to {goto}")]
            break
    return Command(
        goto=goto,
        update={
            "next": goto,
            "messages": agent_message,
            "current_task": state["current_task"]
        }
    )

stinger_workflow = StateGraph(StingerState)

stinger_workflow.add_edge(START, "UserInput")
stinger_workflow.add_node("UserInput", user_input)
stinger_workflow.add_edge("UserInput", "Initializer")
stinger_workflow.add_node("Initializer", initializer)
stinger_workflow.add_edge("Initializer", "StingerAgent")
stinger_workflow.add_node("StingerAgent", stinger_agent)
stinger_workflow.add_node("Recon", recon_graph)
stinger_workflow.add_node("Enum", enum_graph)
#stinger_workflow.add_node("Exploit", exploit_graph)
#stinger_workflow.add_node("PostEx", postex_graph)

stinger_graph = stinger_workflow.compile()

if __name__ == "__main__":
    base_state = StingerState(
        messages= [],
        hosts= {},
        tasks= [],
        context= "",
        next= ""
    )

    testing_state = StingerState(
        messages= [],
        hosts= {},
        tasks= [],
        context= "",
        current_task= -1,
        next= ""
    )

    test_message = HumanMessage(
        "* Scan the target, how many ports are open?\n" #RECON
        "* What version of Apache is running?\n"        #ENUMERATION
        "* What service is running on port 22?\n"       #ENUMERATION
        "* Use GoBuster to find hidden directories. What is the hidden directory?\n"  #ENUMERATION
    )
    testing_state["messages"] = add_messages(testing_state["messages"], test_message)
    testing_state["context"] = "Target machine IP Address is 10.10.243.47"

    stinger_agent(testing_state)
    # stinger_graph.invoke(base_state)

# ROOTME testing state
# {
#   "messages": [
#     {
#       "content": "* Scan the target, how many ports are open?\n* What version of Apache is running?\n* What service is running on port 22?\n* Use GoBuster to find hidden directories. . What is the hidden directory?",
#       "type": "human"
#     }
#   ],
#   "hosts": {},
#   "context": "Target machine IP Address is 10.10.99.108",
#   "current_task": -1,
#   "next": ""
# }


#Blank State
# {
#   "messages": [],
#   "hosts": {},
#   "tasks": [],
#   "context": "",
#   "current_task": -1
#   "next": ""
# }