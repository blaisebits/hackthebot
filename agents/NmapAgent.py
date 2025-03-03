from dotenv import load_dotenv
from langchain.chains.hyde.prompts import arguana

load_dotenv()

# from utils.OpenRouter import ChatOpenRouter
from langchain_anthropic import ChatAnthropic
from langchain.prompts.prompt import PromptTemplate

from utils.LangChain_RoboPages import RoboPages

def scan(task: str, targets: [str]) -> str:
    model = "claude-3-7-sonnet-latest"
    rb = RoboPages()
    tools = rb.filter_tools(filter_string="nmap")

    # llm = ChatAnthropic(
    #     model= model,
    #     temperature=0.55,
    #     tools = tools
    # ).with_structured_output(rb.RoboPagesOutput)
    llm = ChatAnthropic(
        model=model,
        temperature=0.55,
        tools=tools
    ).with_structured_output(rb.RoboPagesOutput)
    llm.bind_tools(tools)

    prompt_template = PromptTemplate.from_template( template="""
You are a expert on the tool Nmap, your primary job is to perform <TASKS> defined below using the provided <TOOLS>
Addition context may be provided and should be taken into consideration.

<TOOLS>
{tools}
</TOOLS>

<TASKS>
{input}
</TASKS>

<CONTEXT>
{agent_scratchpad}
</CONTEXT>
"""
    )
    template = prompt_template.format_prompt(
        tools = tools,
        input = f"{task} : {targets}",
        agent_scratchpad = ""
    )

    tool_query = llm.invoke(
        input = template
    )

    nmap_results = rb.get_tool(tool_query.tool)._run(
        **tool_query.parameters[0]
    )
    return output


if __name__ == "__main__":
    print(
        scan(
            task = "Find common open TCP ports",
            targets = ["scanme.nmap.org"]
        )
    )