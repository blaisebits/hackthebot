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
    """Single Task entity for agents to process.
    Status indicators:
     - new: initially created task
     - working: currently being executed by the agent
     - completed: Agent work completed
     - validated: Agent has validated the task was sufficiently completed
    """
    task: str
    status: Literal["new", "working", "completed", "validated"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]
    tool: List[str] # The tool(s) used to complete the task
    output: List[Dict]
    answer: Optional[TaskAnswer]

class TaskList(TypedDict):
    """Used for structured output"""
    tasks: List[Task]

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    hosts: Dict[str, Host] # e.g. hostname(1.2.3.4)
    tasks: List[Task]
    current_task: int  # points to the list index for tasks field
    context: str
    next: str

class StingerRouter(TypedDict):
    """Agent to route to next. If no workers needed, route to FINISH."""
    next: Literal["Recon","Enum","Exploit","PostEx","FINISH"]
