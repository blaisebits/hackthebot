from typing import Annotated, List, Literal, Optional, Any
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, ToolMessage
from langgraph.graph import add_messages

class Port(TypedDict):
    """Single port on a network entity"""
    port: int
    protocol: str
    state: str
    service: str
    version: str
    cpe: List[str]
    scripts: List[str]

class TaskAnswer(TypedDict):
    question: str
    answer: str
    reason: str

class ExploitTool(TypedDict):
    name: Annotated[str, ..., "The name of the toolcall"]
    args: Annotated[dict, ..., "Exact tool call arguments for exploit"]

class ExploitCode(TypedDict):
    langauge: Annotated[str, ..., "The programming language used for the exploit code"]
    code: Annotated[str, ..., "The exploit code"]

class InitialAccessExploit(TypedDict):
    tool: Optional[Annotated[ExploitTool, ..., "Tool call that can be used for initial access"]]
    code: Optional[Annotated[ExploitCode, ..., "Code that can be used for initial access"]]
    user: Annotated[str, ..., "The username context that executes the exploit code"]
    permissions: Annotated[Literal["low","user","admin","root"], ..., "The relative permissions of the user"]

class Host(TypedDict):
    """Single network entity"""
    ip_address: Annotated[str, ..., "IP address of the host"]
    hostname: Annotated[List[str], ..., "DNS hostname associated to the host."]
    ports: Annotated[dict[str, Port], ..., "Mapping of ports to their attributes."]
    initial_access_exploit: Annotated[dict[int, InitialAccessExploit], ..., "Maps port integer to an initial access exploit."]
    verdicts: Annotated[List[TaskAnswer], ..., "Task verdicts rendered associated to this host for completed task."]

class ExploitStep(TypedDict):
    """Single Task entity for agents to process."""
    iterations: Annotated[int,..., "The number of attempts for completing this step"]
    scratchpad: Annotated[str, ..., "Actions and outcomes taken to complete this ExploitStep"]
    status: Annotated[Literal["new", "working", "validated", "failed", "skipped"],...,"The current status of the exploit step"]
    step_task: Annotated[str, ..., "The action to complete for the ExploitStep"]

class ExploitTask(TypedDict):
    task: Annotated[str, ..., "The exploit method being attempted"]
    status: Annotated[Literal["new", "working", "validated", "failed","exploitable","non-exploitable"], ...,"The current status of the exploit task"]
    # current_step: Annotated[int,...,"List array index value to for the current step"]
    steps: Annotated[list[ExploitStep], ...,"List array of steps to complete the exploit task"]
    target_ip: Annotated[str, ...,"The target host's IP address"]
    initial_access_exploit: Annotated[str, ..., "Payload for single command execution on the target."]

class Task(TypedDict):
    """Single Task entity for agents to process."""
    task: str
    preflightcheck: bool
    status: Literal["new", "working", "validated"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]
    tool: List[str] # The tool(s) used to complete the task
    output: List[dict|ExploitTask] # Formatted Tool output or ExploitTask
    target_ip: str # The target host IP address
    verdict: Optional[TaskAnswer]|None # Answer for Task

class TaskList(TypedDict):
    """Used for structured output"""
    tasks: List[Task]

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    hosts: dict[str, Host] # e.g. 192.168.3.4
    tasks: List[Task]
    current_task: int  # points to the list index for tasks field
    context: List[str|Host]
    persistent_tools: dict[str, Any] #{agent_name:tool}
    next: str #Used for routing to primary agents
    working_memory: str #Only used for internal primary agent information
    longterm_memory: str #only here just in case it's needed
    last_tool_called: ToolMessage


class StingerRouter(TypedDict):
    """Agent to route to next. If no workers needed, route to FINISH."""
    next: Literal["Recon","Enum","Exploit","PostEx","FINISH"]
