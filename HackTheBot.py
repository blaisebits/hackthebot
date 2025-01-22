from utils.OpenRouter import ChatOpenRouter
from langchain.prompts.prompt import PromptTemplate


def main():
    model = "microsoft/phi-4"

    llm = ChatOpenRouter(
        model_name= model,
        temperature= 0.7
    )


if __name__ == "__main__":
    main()