from langchain_core.messages import HumanMessage

from langgraph.graph import START, END, add_messages, StateGraph
from langgraph.types import Command

from agents.ReconAgent import recon_graph
from utils.Configuration import Configuration
from utils.Prompts import get_stinger_prompt_template
from utils.States import StingerState, TaskList

agents = ["Recon",
          "Enum",
          # "Exploit",
          # "PostEx"
          ]

llm = Configuration["llm"]

def user_input(state: StingerState):
    # stub code, will implement later
    human_message = HumanMessage(
        "* Find common open ports on scanme.nmap.org."
    )
    return add_messages(state["messages"],human_message)

"""Called after User input to format initial task list"""
def initializer(state: StingerState):
    raw_tasks = state["messages"][-1].content
    stinger_context = state["context"]

    stinger_prompt_template = get_stinger_prompt_template()
    stinger_prompt = stinger_prompt_template.invoke(
        {
            "tasks": raw_tasks,
            "members": agents,
            "context": stinger_context
        }
    )
    llm_with_structured_output = llm.with_structured_output(TaskList)
    response = llm_with_structured_output.invoke(stinger_prompt)
    # print(response)

    # Checking for and ordering task list
    ordered_task_list = TaskList(tasks=[])
    if response.tool_calls:
        for agent in agents:
            for task in response.toolcalls["tasks"]:
                if task.get("agent") == agent:
                    ordered_task_list["tasks"].append(task)
    return {"tasks": ordered_task_list}


def stinger_agent(state: StingerState):
    tasks = state["tasks"]
    goto = ""
    for task in tasks:
        if task["status"] == "new":
            goto = task["agent"]
    return Command(goto=goto, update={"next": goto})

stinger_workflow = StateGraph(StingerState)

stinger_workflow.add_edge(START, "UserInput")
stinger_workflow.add_node("UserInput", user_input)
stinger_workflow.add_edge("UserInput", "Initializer")
stinger_workflow.add_node("Initializer", initializer)
stinger_workflow.add_edge("Initializer", "StingerAgent")
stinger_workflow.add_node("StingerAgent", stinger_agent)
stinger_workflow.add_node("Recon", recon_graph)



if __name__ == "__main__":
    testing_state = StingerState(
        messages= [],
        hosts= {},
        tasks= [],
        context= "",
        next= ""
    )

    test_message = HumanMessage(
        "* Scan the target, how many ports are open?\n" #RECON
        "* What version of Apache is running?\n"        #ENUMERATION
        "* What service is running on port 22?\n"       #ENUMERATION
        "* Use GoBuster to find hidden directories.\n"  #ENUMERATION
    )
    testing_state["messages"] = add_messages(testing_state["messages"], test_message)
    testing_state["context"] = "Target machine is 127.0.0.1"

    stinger_agent(testing_state)
