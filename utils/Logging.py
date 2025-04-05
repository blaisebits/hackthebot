from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import datetime

class ConsoleColors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'

log_file = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+".log"

def log_message(text:str):
    date_time_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f = open(log_file, "w")
    f.write(f"{date_time_string}\n{text}")
    f.close()

def print_debug(text:str, log:bool=False):
    header = "==================================== DEBUG ====================================="
    print(ConsoleColors.RED + header + ConsoleColors.RESET)
    print(text)
    if log: log_message(f"{header}\n{text}\n\n")

def print_unknown(text:str, log:bool=False):
    header = "=================================== UNKNOWN ===================================="
    print(ConsoleColors.RED + header + ConsoleColors.RESET)
    print(text)
    if log: log_message(f"{header}\n{text}\n\n")

def print_msg_ai(text:str, log:bool=False):
    header = "================================== Ai Message =================================="
    print(ConsoleColors.GREEN + header + ConsoleColors.RESET)
    print(text)
    if log: log_message(f"{header}\n{text}\n\n")

def print_msg_human(text:str, log:bool=False):
    header = "================================ Human Message ================================="
    print(ConsoleColors.BLUE + header + ConsoleColors.RESET)
    print(text)
    if log: log_message(f"{header}\n{text}\n\n")

def print_msg_toolcall(text:str, log:bool=False):
    header = "================================ Tool Message =================================="
    print(ConsoleColors.CYAN + text + ConsoleColors.RESET)
    print(text)
    if log: log_message(f"{header}\n{text}\n\n")

def print_agent_message(message: AIMessage|HumanMessage|ToolMessage, log:bool=False):
    msg = message.text()
    if message.type == 'ai':
        print_msg_ai(msg, log)
    elif message.type == 'human':
        print_msg_human(msg, log)
    elif message.type == 'tool':
        print_msg_toolcall(msg, log)
    else:
        print_unknown(msg, log)
