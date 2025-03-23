# https://langchain-ai.github.io/langgraph/how-tos/tool-calling/#manually-call-toolnode
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import ToolNode

from utils.LangChain_RoboPages import RoboPages

from dotenv import load_dotenv
load_dotenv()

def toolagent():
    model = "claude-3-7-sonnet-latest"
    rb = RoboPages()
    nmap_tools = rb.filter_tools(filter_string="nmap")
    tool_node = ToolNode(nmap_tools)

    llm = model = ChatAnthropic(
            model=model,
            temperature=0.55
        )