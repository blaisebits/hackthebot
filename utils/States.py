from typing import Annotated, List, Dict, Tuple, Literal, Optional
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from utils.Configuration import Config
from utils.OutputFormatters import NmapOutputFormat

"""Single port on a network entity"""
class Port(TypedDict):
    port: int
    protocol: str
    state: str
    service: str
    version: str
    scripts: List[str]

class Host(TypedDict):
    """Single network entity"""
    ip_address: str
    hostname: Optional[str]
    ports: Dict[str, Port] # example {"22/tcp":{ Port({..} }

class Task(TypedDict):
    """Single Task entity for agents to process.
    Status indicators:
     - new: initially created task
     - working: currently being executed by the agent
     - completed: Agent work completed
     - validated: Stinger has validated the task was sufficiently completed
    """
    task: str
    status: Literal["new", "working", "completed", "validated"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]
    tool: str # The tool used to complete the task
    output: Dict

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
