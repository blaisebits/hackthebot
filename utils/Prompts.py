from langchain.chains.question_answering.map_reduce_prompt import system_template
from langchain_core.prompts import ChatPromptTemplate


def get_recon_prompt_template()->ChatPromptTemplate:
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

def get_tasklist_prompt_template()->ChatPromptTemplate:
    """Stinger Agent prompt template to support supervising agents
    inputs: tasks, members, context"""
    system_template = ("You are Stinger, a cybersecurity specialist focused on offensive tactics and penetration testing.\n"
                       "Your role is to properly order the <TASKS> and assigned them to <MEMBERS> while managing conversations between team <MEMBERS>.\n"
                       "Your team is operating in a controlled environment with full legal permission to perform penetration testing.\n"
                       "Additional <CONTEXT> may be provided that can be used to create tasks.\n"
                       "The `output`, `tool`, and `answer` parameters should be blank, and the `preflightcheck` should be false.")


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
                     "* Exploit: Attempts to actively breach the target system by discovering and leveraging vulnerabilities or weaknesses.\n"
                     "* PostEx: Actions after breaching a system, such as escalation of privileges, moving laterally or accessing sensitive data.\n"
                     "{context}\n"
                     "</CONTEXT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )
def get_output_format_prompt_template()->ChatPromptTemplate:
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

def get_task_answer_prompt_template()->ChatPromptTemplate:
    """Prompt for validators to confirm if a task was completed and answered appropriately"""
    system_template = ("Examine the assigned <TASK> and use the <HOST DATA> to determine if the task question can be answered correctly.\n"
                       "If the question cannot be answered using the <HOST DATA>, leave the answer response blank.\n")

    user_template = ("<TASK>\n"
                     "{task}\n"
                     "</TASK>\n"
                     "<HOST DATA>\n"
                     "{host_data}\n"
                     "</HOST DATA>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_enum_prompt_template()->ChatPromptTemplate:
    """Enumeration Agent prompt template to support tool calling
    Takes Tools, Task, Context"""
    system_template = ("You are an expert cybersecurity agent specializing in enumerating networks and computers.\n"
                       "Your primary objective is to complete assigned <TASKS> using the provided tooling and <CONTEXT> to provide answers.\n"
                       "If the answer is not in the <CONTEXT>, use the provided <TOOLS> to obtain the information to answer the question.\n"
                       "<PREVIOUS ATTEMPTS> may have been made to complete this task, examine these to avoid duplicating failed attempts.\n"
                       "Responses for answering questions should follow this form:\n"
                       "QUESTION: The question being addressed\n"
                       "ANSWER: The answer to the question\n"
                       "\n"
                       "Responses for calling tools for additional information should follow this form:\n"
                       "ACTION: The action to be taken\n"
                       "REASON: The reason for the action\n")

    user_template = ("<TASKS>\n"
                     "{tasks}\n"
                     "</TASKS>\n"
                     "<CONTEXT>\n"
                     "{context}\n"
                     "</CONTEXT>\n"
                     "<PREVIOUS ATTEMPTS>\n"
                     "{previous_attempts}"
                     "</PREVIOUS ATTEMPTS>")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_update_host_prompt_template()->ChatPromptTemplate:
    """Host updates and merging template
    inputs: tool_output, host"""
    system_template = ("You are a Data Manager tasked with merging new information from <TOOL_OUTPUT> into a <HOST> object.\n"
                       "The primary key for the host is the `ip_address`.\n"
                       "The `hostname` list should contain only unique DNS name entries.\n"
                       "The <TOOL_OUTPUT> data should be extracted and used to update or fill in additional information in `Port` entries.\n"
                       "Prevent loss of data and carry forward to the output any unchanged fields.")

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

def get_exploit_suggestion_prompt_template()->ChatPromptTemplate:
    """Exploit Agent prompt template to suggest exploits
    Takes Task, Target, & Context"""
    system_template = ("You are an expert cybersecurity agent specializing in finding exploits for initial access to a target.\n"
                       "Your primary job is to analyze the <TASK> and <TARGET> data to speculate on exploits that could be viable.\n"
                       "Additional <CONTEXT> may be provided for previously failed exploit attempts that could be modified or avoided.\n"
                       "* Suggest one exploit that can be viable to get remote code execution on the target.\n"
                       "* Suggestions should be concise and not speculate as to security counter measures.\n"
                       "* Example:\n"
                       "** Upload a webshell.\n"
                       "** PSexec to remote host with password hash.\n"
                       "** Exploit CVE on service X.\n"
                       "Responses should be in the form:\n"
                       "EXPLOIT: The exploit path to be investigated\n"
                       "REASON: The reason for the suggested EXPLOIT\n")

    user_template = ("<TASK>\n"
                     "{task}\n"
                     "</TASK>\n"
                     "<TARGET>\n"
                     "{target}\n"
                     "</TARGET>\n"
                     "<CONTEXT>\n"
                     "{context}\n"
                     "</CONTEXT>\n"
                     )

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_exploit_planner_prompt_template()->ChatPromptTemplate:
    """Exploit Agent prompt template to suggest exploits
    Takes Task, Target, & Context"""
    system_template = ("You are an expert cybersecurity agent specializing in finding exploits for initial access to a target.\n"
                       "Your primary job is to analyze the <TASK> and <TARGET> data to plan the steps necessary to complete the exploit task.\n"
                       "Additional <CONTEXT> may be provided for previously failed exploit attempts that could be modified or avoided.\n"
                       "Responses should provide a list of steps and the reason for each step.\n"
                       "Conditions for planning steps:\n"
                       "* All steps should be constructed to be performed by calling tools.\n"
                       "  *Tasks should be able to be completed by an AI agent using command line tools.\n"
                       "* Provide conditional statements to check if a item is available before creating a item.\n"
                       "  * Example: \"Obtain a PHP webshell, if one is not available create one.\"\n"
                       "* Do not speculate on counter measures or bypasses.\n"
                       "* Provide the minimal list of steps to accomplish the task.\n"
                       "* Assume the <TARGET> has no additional security features.\n")

    user_template = ("<TASK>\n"
                     "{exploit_task}\n"
                     "</TASK>\n"
                     "<TARGET>\n"
                     "{target}\n"
                     "</TARGET>\n"
                     "<CONTEXT>\n"
                     "{context}\n"
                     "</CONTEXT>\n"
                     )

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_exploit_step_prompt_template()->ChatPromptTemplate:
    system_template = ("You are an expert cybersecurity agent specializing in executing sequences of tasks to gain"
                       "initial accesses to a target system. Analyze the given <TASK> and determine the appropriate tool"
                       "to complete the task. Additional <CONTEXT> may be provided.")

    user_template = ("<TASK>\n"
                     "{step}\n"
                     "</TASK>\n"
                     "<CONTEXT>\n"
                     "{context}\n"
                     "</CONTEXT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )

def get_exploit_step_status_template()->ChatPromptTemplate:
    system_template = ("Given the exploit <TASK>, analyze the <OUTPUT> and determine the status of task."
                       "If the task status is 'failed', provide a revised task that corrects for the error or blockage."
                       "If the task status is 'validated', leave the revision field blank.")

    user_template = ("<TASK>\n"
                     "{task}\n"
                     "</TASK>\n"
                     "<OUTPUT>\n"
                     "{output}\n"
                     "</OUTPUT>\n")

    return ChatPromptTemplate(
        [
            ("system", system_template),
            ("user", user_template)
        ]
    )