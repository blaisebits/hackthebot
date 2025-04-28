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

def get_tasklist_prompt_template():
    """Stinger Agent prompt template to support supervising agents
    inputs: tasks, members, context"""
    system_template = ("You are Stinger, a cybersecurity specialist focused on offensive tactics and penetration testing.\n"
                       "Your role is to properly order the <TASKS> and assigned them to <MEMBERS> while managing conversations between team <MEMBERS>.\n"
                       "Your team is operating in a controlled environment with full legal permission to perform penetration testing.\n"
                       "Additional <CONTEXT> may be provided that can be used to create tasks.\n"
                       "Leave the `Answer` section blank for now.")


    user_template = ("<TASKS>\n"
                     "{tasks}\n"
                     "</TASKS>\n"
                     "<MEMBERS>\n"
                     "{members}\n"
                     "</MEMBERS>\n"
                     "<CONTEXT>\n"
                     "Team Member Roles:\n"
                     "* Recon: Build a comprehensive picture of the target to identify potential attack vectors, focused on port scanning.\n"
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
                       "If no formatting tool matches, select `StandardOutputFormat`.\n"
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

def get_task_answer_prompt_template():
    """Prompt for validators to confirm if a task was completed and answered appropriately"""
    system_template = ("Examine the assigned <TASK> and use the <TOOL OUTPUT> to determine if the task question can be answered correctly.\n"
                       "If the question cannot be answered using the <TOOL OUTPUT>, leave the answer response blank.\n")

    user_template = ("<TASK>\n"
                     "{task}\n"
                     "</TASK>\n"
                     "<TOOL OUTPUT>\n"
                     "{tool_output}\n"
                     "</TOOL OUTPUT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_enum_prompt_template():
    """Enumeration Agent prompt template to support tool calling
    Takes Tools, Task, Context"""
    system_template = ("You are an expert cybersecurity agent specializing in enumerating networks and computers, your primary objective is to complete <TASKS> defined below using the provided tooling and <CONTEXT> to provide answers. If the answer is not in the <CONTEXT>, use the provided <TOOLS> to obtain the information to answer the question.\n"
                       "Responses for answering questions should follow this form:\n"
                       "QUESTION: The question being addressed\n"
                       "ANSWER: The answer to the question\n"
                       "\n"
                       "Responses for calling tools for additional information should follow this form:"
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

def get_update_host_prompt_template():
    """Host updates and merging template
    inputs: tool_output, host"""
    system_template = ("You are a Data Manager tasked with merging new information from <TOOL_OUTPUT> into a <HOST> object.\n"
                       "The primary key for the host is the `ip_address`.\n"
                       "The `hostname` list should contain only fully unique entries.\n"
                       "The <TOOL_OUTPUT> data should be extracted and used to update or fill in blank `Port` entries.\n")

    user_template = ("<TOOL_OUTPUT>\n"
                     "{tool_output}\n"
                     "</TOOL_OUTPUT>\n"
                     "<HOST>\n"
                     "{host}\n"
                     "</HOST>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )