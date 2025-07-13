from typing import Optional, Any
from anthropic import APIStatusError
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from typing_extensions import TypedDict
from dotenv import load_dotenv
load_dotenv()

from utils.LangChain_RoboPages import RoboPages, RoboPagesTool
rb = RoboPages()

class Config(TypedDict):
    model: str
    model_temp: float
    llm: BaseChatModel
    robopages_tools:list[RoboPagesTool]

__DEFAULT_MODEL= "claude-3-7-sonnet-latest"
__DEFAULT_MODEL_TEMP= 0.70
__DEFAULT_LLM= ChatAnthropic( model= __DEFAULT_MODEL, temperature= __DEFAULT_MODEL_TEMP )

Configuration = Config(
    model=__DEFAULT_MODEL,
    model_temp=__DEFAULT_MODEL_TEMP,
    llm=__DEFAULT_LLM,
    robopages_tools=rb.get_tools()
)

