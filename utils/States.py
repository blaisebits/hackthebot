from typing import Annotated, List, Dict, Literal, Optional, Any
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
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

class Host(TypedDict):
    """Single network entity"""
    ip_address: Annotated[str, ..., "IP address of the host"]
    hostname: Annotated[List[str], ..., "DNS hostname associated to the host."]
    ports: Annotated[Dict[str, Port], ..., "Mapping of ports to their attributes."]
    initial_access_exploit: Annotated[str, ..., "Payload for single command execution on the target."]
    verdicts: Annotated[List[TaskAnswer], ..., "Task verdicts rendered associated to this host for completed task."]

class ExploitStep(TypedDict):
    """Single Task entity for agents to process."""
    step_task: str
    status: Literal["new", "working", "validated", "failed", "skipped"]
    tool: List[str] # The tool(s) used to complete the task
    output: List[Dict] # output_formatted tool call output

class ExploitTask(TypedDict):
    task: str
    status: Literal["new", "working", "validated", "failed"]
    verdict: Literal["exploitable","non-exploitable"]|None
    current_step: int
    steps: List[ExploitStep]
    target_ip: str  # The target host IP address
    initial_access_exploit: Annotated[str, ..., "Payload for single command execution on the target."]

class Task(TypedDict):
    """Single Task entity for agents to process."""
    task: str
    preflightcheck: bool
    status: Literal["new", "working", "validated"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]
    tool: List[str] # The tool(s) used to complete the task
    output: List[Dict|ExploitTask] # Formatted Tool output or ExploitTask
    target_ip: str # The target host IP address
    verdict: Optional[TaskAnswer]|None # Answer for Task

class TaskList(TypedDict):
    """Used for structured output"""
    tasks: List[Task]

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    hosts: Dict[str, Host] # e.g. 192.168.3.4
    tasks: List[Task]
    current_task: int  # points to the list index for tasks field
    context: List[str|Host]
    persistent_tools: Dict[str, Any] #{agent_name:tool}
    next: str

class StingerRouter(TypedDict):
    """Agent to route to next. If no workers needed, route to FINISH."""
    next: Literal["Recon","Enum","Exploit","PostEx","FINISH"]
