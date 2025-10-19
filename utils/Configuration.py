from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from typing_extensions import TypedDict
from dotenv import load_dotenv
load_dotenv()

from os import getenv

class Config(TypedDict):
    llm: BaseChatModel

__CLAUDE_MODEL= "claude-3-7-sonnet-latest"
__CLAUDE_MODEL_TEMP= 0.70
__CLAUDE_LLM= ChatAnthropic(
        model= __CLAUDE_MODEL,
        temperature= __CLAUDE_MODEL_TEMP
    )

# __OLLAMA_MODEL= "gpt-oss:20B"
# __OLLAMA_MODEL_TEMP= 0.70
# __OLLAMA_LLM= ChatOpenAI(
#         model= __OLLAMA_MODEL,
#         temperature= __OLLAMA_MODEL_TEMP,
#         openai_api_key="foobar",
#         openai_api_base= getenv("OLLAMA_BASE_URL")
#     )

_LLM = __CLAUDE_LLM

Configuration = Config(
    llm=_LLM
)

