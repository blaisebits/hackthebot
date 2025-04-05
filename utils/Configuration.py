from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from typing_extensions import TypedDict

from dotenv import load_dotenv
load_dotenv()

class Config(TypedDict):
    model: str
    model_temp: float
    llm: BaseChatModel

__DEFAULT_MODEL= "claude-3-7-sonnet-latest"
__DEFAULT_MODEL_TEMP= 0.99
__DEFAULT_LLM= ChatAnthropic( model= "claude-3-7-sonnet-latest", temperature= 0.55 )

Configuration = Config(
    model=__DEFAULT_MODEL,
    model_temp=__DEFAULT_MODEL_TEMP,
    llm=__DEFAULT_LLM
)