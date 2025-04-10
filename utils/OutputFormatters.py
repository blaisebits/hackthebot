from typing import Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class NmapOutputFormat(BaseModel):
    ip_address: str = Field(description="The host ip address")
    ports: List[str] = Field(description="The port number")
    states: List[str] = Field(description="Define if the port is open, closed, or filtered")
    services: List[str] = Field(description="The service running on the associated port")
    versions: List[str] = Field(description="The version of the server software running")
    scripts: List[List[str]] = Field(description="Nmap Scripting engine output")

class GoBusterOutputFormat(BaseModel):
    target: str = Field(description="Target scanned")

tool_parsers = [
    NmapOutputFormat,
    GoBusterOutputFormat
]