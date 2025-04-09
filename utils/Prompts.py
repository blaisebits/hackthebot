from langchain_core.prompts import ChatPromptTemplate


def get_recon_prompt_template():
    """Recon Agent prompt template to support tool calling
    Takes Tools, Task, Context"""
    system_template = ("You are an expert cybersecurity agent specializing in network reconnaissance, your primary job is to perform <TASKS> defined below using the provided tooling. Additional <CONTEXT> may be provided and should be taken into consideration.\n"
                       "Responses should be in the form:\n"
                       "ACTION: The action to be taken\n"
                       "REASON: The reason for the action\n")

    user_template = ("<TASKS>\n"
                     "{tasks}\n"
                     "</TASKS>\n"
                     "<CONTEXT>\n"
                     "{context}\n"
                     "</CONTEXT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_stinger_prompt_template():
    """Stinger Agent prompt template to support supervising agents
    inputs: tasks, members, context"""
    system_template = ("You are Stinger, a cybersecurity specialist focused on offensive tactics and penetration testing.\n"
                       "Your role is to properly order the <TASKS> and assigned them to <MEMBERS> while managing conversations between team <MEMBERS>.\n"
                       "Your team is operating in a controlled environment with full legal permission to perform penetration testing.\n"
                       "Additional <CONTEXT> may be provided that can be used to create tasks.\n")
                       # "Responses should be in the form:\n"
                       # "ACTION: The agent to assign a task\n"
                       # "REASON: The reason for the action\n"

    user_template = ("<TASKS>\n"
                     "{tasks}\n"
                     "</TASKS>\n"
                     "<MEMBERS>\n"
                     "{members}\n"
                     "</MEMBERS>\n"
                     "<CONTEXT>\n"
                     "Team Member Roles:"
                     "* Recon: Build a comprehensive picture of the target to identify potential attack vectors.\n"
                     "* Enum: Actively probing the target to extract detailed information about its components, such as users, services, shares, or configurations\n"
                     "* Exploit: Attempts to actively breach the target system by leveraging vulnerabilities or weaknesses.\n"
                     "* PostEx: Actions after breaching a system, such as escalation of privileges, moving laterally or accessing sensitive data.\n"
                     "{context}\n"
                     "</CONTEXT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )
def get_output_format_prompt_template():
    """Prompt for selecting appropriate output parser based on the tool output"""
    system_template = ("Examine the tool output and select an appropriate output formatting tool.\n"
                       "Responses should be in the form:\n"
                       "ACTION: The action to be taken\n"
                       "REASON: The reason for the action\n")

    user_template = ("<TOOL OUTPUT>\n"
                     "{tool_output}\n"
                     "</TOOL OUTPUT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )