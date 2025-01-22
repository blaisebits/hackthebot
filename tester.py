## TEMP IMPORTS
import os
from langchain_core.prompts import ChatPromptTemplate

### Perm Imports
from utils.OpenRouter import ChatOpenRouter
from langchain.prompts.prompt import PromptTemplate

#######################################
def main():
        ## Testing LLM
    # model = "microsoft/phi-4"
    #
    # llm = ChatOpenRouter(
    #     model_name= model,
    #     temperature=0.55
    # )
    # prompt = ChatPromptTemplate.from_template("tell me a short joke about {topic}")
    # openrouter_chain = prompt | llm
    # response = openrouter_chain.invoke({"topic": "warhammer 40k"})
    # print(response.content)
    #
    # prompt = ChatPromptTemplate.from_template("What was the last question I asked?")
    # openrouter_chain = prompt | llm
    # response = openrouter_chain.invoke({})
    # print(response.content)


if __name__ == "__main__":
    main()