from typing import Annotated, List, Dict, Literal, Optional
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

class Host(TypedDict):
    """Single network entity"""
    ip_address: str
    hostname: List[str]
    ports: Dict[str, Port] # example {"22/tcp":{ Port({..} }

class TaskAnswer(TypedDict):
    question: str
    answer: str

class Task(TypedDict):
    """Single Task entity for agents to process."""
    task: str
    preflightcheck: bool
    status: Literal["new", "working", "validated"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]
    tool: List[str] # The tool(s) used to complete the task
    output: List[Dict] # output_formatted tool call output
    target_ip: str # The target host IP address
    answer: Optional[TaskAnswer] # Answer for Task

class TaskList(TypedDict):
    """Used for structured output"""
    tasks: List[Task]

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    hosts: Dict[str, Host] # e.g. 192.168.3.4
    tasks: List[Task]
    current_task: int  # points to the list index for tasks field
    context: List[str|Host]
    next: str

class StingerRouter(TypedDict):
    """Agent to route to next. If no workers needed, route to FINISH."""
    next: Literal["Recon","Enum","Exploit","PostEx","FINISH"]
