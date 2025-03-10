from dotenv import load_dotenv
load_dotenv()

import argparse
import pprint
# from utils.OpenRouter import ChatOpenRouter
from langchain_anthropic import ChatAnthropic
from langchain.prompts.prompt import PromptTemplate

from utils.LangChain_RoboPages import RoboPages
from utils.OutputFormatters import NmapOutputFormat

def scan(task: str, targets: [str]) -> dict:
    model = "claude-3-7-sonnet-latest"
    rb = RoboPages()
    tools = rb.filter_tools(filter_string="nmap")

    base_llm = ChatAnthropic(
        model=model,
        temperature=0.55
    )
    #LLM instance used to choose a function and parameters
    llm_select_tool = base_llm
    llm_select_tool.bind_tools(tools)
    llm_select_tool = base_llm.with_structured_output(rb.RoboPagesOutput)

    #LLM instance used to parse the Nmap output into a pydantic model
    llm_parse_response = base_llm.with_structured_output(NmapOutputFormat)

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
    template1 = prompt_template.format_prompt(
        tools = tools,
        input = f"{task} : {targets}",
        agent_scratchpad = ""
    )

    tool_query = llm_select_tool.invoke(
        input = template1
    )

    nmap_results = rb.get_tool(tool_query.tool)._run(
        **tool_query.parameters
    )

    template2 = prompt_template.format_prompt(
        tools="",
        input=f"{task} : {targets}",
        agent_scratchpad=nmap_results
    )

    nmap_parsed_raw = llm_parse_response.invoke(
        input = template2
    )

    ip_address = nmap_parsed_raw.ip_address
    host_data = {
        "ip_address": ip_address,
        "ports": {}
    }

    #itterate over the ports to get the index and correlate the arrays into a dict
    for index, element in enumerate(nmap_parsed_raw.ports):
        host_data["ports"][element] = {
                "state": nmap_parsed_raw.states[index],
                "Service": nmap_parsed_raw.services[index],
                "version": nmap_parsed_raw.versions[index],
                "scripts": nmap_parsed_raw.scripts[index]
            }


    return host_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        type= str,
        default= "scanme.nmap.org",
        help= "Nmap scan target"
    )
    parser.add_argument(
        "--task",
        type = str,
        default="Find common open TCP ports",
        help="Task to complete"
    )
    options  = parser.parse_args()

    output = scan(
                task = options.task,
                targets = [options.target]
            )

    pprint(output)