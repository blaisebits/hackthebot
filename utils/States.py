from typing import Annotated, List, Dict, Tuple, Literal, Optional
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

from utils.Configuration import Config
from utils.OutputFormatters import NmapOutputFormat

"""Single port on a network entity"""
class Port(TypedDict):
    port_num: int
    protocol: str
    state: str
    service: str
    version: str
    scripts: List[str]

"""Single network entity"""
class Host(TypedDict):
    ip_address: str
    ports: Dict[str, Port]

class Task(TypedDict):
    task: str
    status: Literal["new", "working", "completed"]
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"]

"""Used for structured output"""
class TaskList(TypedDict):
    tasks: List[Task]

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    hosts: Dict[str, Host]
    tasks: List[Task]
    context: str
    next: str

class StingerRouter(TypedDict):
    """Agent to route to next. If no workers needed, route to FINISH."""
    next: Literal["Recon","Enum","Exploit","PostEx","FINISH"]

class ReconState(TypedDict):
    tasks: List[Task]
    hosts: Dict[str, Host]
    context: str
    messages: Annotated[list[AnyMessage], add_messages]