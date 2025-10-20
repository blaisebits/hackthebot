from typing import Literal
import pickle

from langchain_core.messages import HumanMessage, AIMessage

from langgraph.graph import START, add_messages, StateGraph
from langgraph.types import Command

from agents.EnumAgent import enum_graph
from agents.ExploitAgent import exploit_graph
from agents.ReconAgent import recon_graph
from utils.Configuration import Configuration
from utils.LLMHelpers import llm_invoke_retry
from utils.OutputFormatters import TaskBasicInfoList
from utils.Prompts import get_tasklist_prompt_template
from utils.States import StingerState, TaskList
from utils.Tasking import expand_task_basic_info

import docker
from docker.errors import NotFound
docker_socket = docker.from_env()
try:
    docker_socket.volumes.get("hackthebot")
except NotFound:
    docker_socket.volumes.create("hackthebot")
except Exception as e:
    print(f"Docker failure. Try Harder.\n{e}")


agents = ["Recon",
          "Enum",
          "Exploit",
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
    stinger_context = state["context"]

    tasklist_prompt_template = get_tasklist_prompt_template()
    tasklist_prompt = tasklist_prompt_template.invoke(
        {
            "tasks": raw_tasks,
            "members": agents,
            "context": stinger_context
        }
    )
    llm_with_structured_output = llm.with_structured_output(TaskBasicInfoList)
    response = llm_invoke_retry(llm_with_structured_output,tasklist_prompt)

    unordered_task_list = []
    for task in response.tasks:
        unordered_task_list.append(expand_task_basic_info(task))

    # Checking for and ordering task list by agent: Recon -> Enum -> Exploit -> PostEx
    ordered_task_list = []
    for task in unordered_task_list:
        for agent in agents:
            if task["agent"] == agent:
                ordered_task_list.append(task)
    return {
        "tasks": ordered_task_list
    }


def stinger_agent(state: StingerState) -> Command[Literal["Recon","Enum","Exploit","StingerHandOff"]]:
    p_tools = {"stinger":"PLACEHOLDER"}
    goto = ""
    agent_message = ""
    for index, task in enumerate(state["tasks"]):
        if task["status"] == "new":
            goto = task["agent"]
            state["current_task"] = index
            agent_message = [AIMessage(f"StingerAgent: Passing to {goto}")]
            break

    if not goto:
        return Command( goto="StingerHandOff" )
    else:
        return Command(
            goto=goto,
            update={
                "next": goto,
                "messages": agent_message,
                "current_task": state["current_task"],
                "persistent_tools": p_tools
            }
        )

def handoff(state: StingerState):
    with open('data.pickle', 'wb') as file:
        pickle.dump(state, file)

    return state


stinger_workflow = StateGraph(StingerState)

stinger_workflow.add_edge(START, "UserInput")
stinger_workflow.add_node("UserInput", user_input)
stinger_workflow.add_edge("UserInput", "Initializer")
stinger_workflow.add_node("Initializer", initializer)
stinger_workflow.add_edge("Initializer", "StingerAgent")
stinger_workflow.add_node("StingerAgent", stinger_agent)
stinger_workflow.add_node("StingerHandOff", handoff)
stinger_workflow.add_node("Recon", recon_graph)
stinger_workflow.add_node("Enum", enum_graph)
stinger_workflow.add_node("Exploit", exploit_graph)
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
