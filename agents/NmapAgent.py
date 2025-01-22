from utils.OpenRouter import ChatOpenRouter
from langchain.prompts.prompt import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain import hub
import tools.Nmap as Nmap

def scan(targets: [str]) -> str:
    model = "microsoft/phi-4"

    llm = ChatOpenRouter(
        model_name= model,
        temperature=0.55
    )

    template = \
"""
Given the list of targets discover which network ports are open
Targets: {targets}
"""
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["targets"]
    )

    tools_for_agents = [
        Tool(
            name="Nmap Small Scan",
            func=Nmap.nmap_port_scan_small,
            description="Useful for quickly scanning the top 100 likely ports"
        ),
        Tool(
            name="Nmap Medium Scan",
            func=Nmap.nmap_port_scan_medium,
            description="Useful for quickly scanning the top 1000 likely ports"
        ),
        Tool(
            name="Nmap Large Scan",
            func=Nmap.nmap_port_scan_large,
            description="Useful for quickly scanning the top 4000 likely ports"
        ),
        Tool(
            name="Nmap Huge Scan",
            func=Nmap.nmap_port_scan_large,
            description="Useful for scanning for all open ports"
        ),
    ]

    react_prompt = hub.pull("hwchase17/react")

    agent = create_react_agent(
        llm=llm,
        tools=tools_for_agents,
        prompt=react_prompt
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools_for_agents,
        verbose=True
    )

    #Checks for more than one target
    target_list = targets[0] if len(targets) == 1 else ", ".join(targets)

    agent_input = {
        "input": prompt_template.format_prompt(targets=target_list)
    }
    result = agent_executor.invoke( input = agent_input)
    return result["output"]

if __name__ == "__main__":
    print(scan(["scanme.nmap.org"]))