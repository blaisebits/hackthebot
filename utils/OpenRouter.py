from dotenv import load_dotenv
load_dotenv()

from typing import Optional
from os import getenv
from langchain_community.chat_models import ChatOpenAI

## Copied from article: https://medium.com/@gal.peretz/openrouter-langchain-leverage-opensource-models-without-the-ops-hassle-9ffbf0016da7
class ChatOpenRouter(ChatOpenAI):
    openai_api_base: str
    openai_api_key: str
    model_name: str
    temperature: float

    def __init__(self,
                 model_name: str,
                 openai_api_key: Optional[str] = None,
                 openai_api_base: str = "https://openrouter.ai/api/v1",
                 temperature: Optional[float] = 0.7,
                 **kwargs):
        openai_api_key = openai_api_key or getenv('OPENROUTER_API_KEY')
        super().__init__(openai_api_base=openai_api_base,
                         openai_api_key=openai_api_key,
                         temperature=temperature,
                         model_name=model_name,
                         **kwargs
                         )