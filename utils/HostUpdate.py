from langchain_core.messages import AIMessage

from utils.Configuration import Configuration
from utils.Prompts import get_update_host_prompt_template
from utils.States import StingerState, Host

llm = Configuration["llm"]

def host_update(state: StingerState):
    """Merges scan data into Host value"""

    current_task = state["tasks"][ state["current_task"] ]
    host_data = state["hosts"][ current_task["target_ip"] ]
    tool_output = current_task["output"][-1] # get last tool output

    update_host_prompt_template = get_update_host_prompt_template()
    update_host_prompt = update_host_prompt_template.invoke(
        {
            "tool_output": tool_output,
            "host": host_data,
        }
    )
    llm_with_structured_output = llm.with_structured_output(Host)

    state["hosts"][ current_task["target_ip"] ] = llm_with_structured_output.invoke(update_host_prompt)

    return {
        "hosts": state["hosts"],
        "messages": [AIMessage(f"HostUpdate: Updated host {current_task["target_ip"]} with scan data from {current_task["tool"][-1]}.")]
    }

def get_stub_host(ip_address: str):
    return Host(
                ip_address=ip_address,
                hostname=[],
                ports={}
            )