from typing import Annotated, List, Dict
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

class StingerState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    node_path: List[str]
    hosts: Dict[str, Host]
    tool_calls: List[str]

class ReconState(TypedDict):
    tasks: str
    hosts: Dict[str, Host]
    context: str
    messages: Annotated[list[AnyMessage], add_messages]