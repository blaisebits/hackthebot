from dotenv import load_dotenv
load_dotenv()

from utils.OpenRouter import ChatOpenRouter
from langchain.prompts.prompt import PromptTemplate
from langchain_core.tools import Tool
from langchain.agents import (
    create_react_agent,
    AgentExecutor,
)
from langchain import hub
from utils.LangChain_RoboPages import RoboPages

def scan(targets: [str]) -> str:
    model = "microsoft/phi-4"

    llm = ChatOpenRouter(
        model_name= model,
        temperature=0.55
    )

    template = \
"""
Given the list of targets discover which common network ports are open
Targets: {targets}
"""
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["targets"]
    )

    react_prompt = hub.pull("hwchase17/react")

    rb = RoboPages()
    tools_for_agents = rb.get_tools()

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
    result = agent_executor.invoke( input = agent_input )
    return result["output"]

if __name__ == "__main__":
    print(scan(["scanme.nmap.org"]))