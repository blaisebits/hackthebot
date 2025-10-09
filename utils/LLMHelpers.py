from anthropic import APIStatusError, RateLimitError
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import Runnable
from langchain_core.runnables.utils import Output
from retry import retry


@retry(exceptions=(APIStatusError,RateLimitError), tries=3, delay=10)
def llm_invoke_retry(llm: Runnable, prompt: PromptValue) -> Output:
    """
    Retry LLM calls incase API errors are being returned
    """
    if isinstance(llm, Runnable):
        if isinstance(prompt, PromptValue):
            return llm.invoke(prompt)
        else:
            raise TypeError(f"prompt expected type PromptValue, got {type(prompt)}.")
    else:
        raise TypeError(f"llm expected type Runnable, got {type(llm)}.")