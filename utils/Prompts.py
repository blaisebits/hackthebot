from langchain_core.prompts import ChatPromptTemplate

def get_recon_prompt_template():
    """Recon Agent prompt template to support tool calling
    Takes Tools, Task, Context"""
    system_template = ("You are an expert cybersecurity agent specializing in network reconnaissance, your primary job is to perform <TASKS> defined below using the provided tooling. Additional <CONTEXT> may be provided and should be taken into consideration."
                       "Responses should be concise stating only the ACTION to be taken and REASON for the action")

#     <TOOLS>
# {tools}
# </TOOLS>
    user_template = """<TASKS>
{tasks}
</TASKS>

<CONTEXT>
{context}
</CONTEXT>"""

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )