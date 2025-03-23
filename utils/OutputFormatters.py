from typing import Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


class RoboPagesOutput(BaseModel):
    tool: str = Field(description="The tool that was used")
    parameters: Dict = Field(description="The parameters for the requested tool")

class NmapOutputFormat(BaseModel):
    ip_address: str = Field(description="The host ip address")
    ports: List[str] = Field(description="The port number")
    states: List[str] = Field(description="Define if the port is open, closed, or filtered")
    services: List[str] = Field(description="The service running on the associated port")
    versions: List[str] = Field(description="The version of the server software running")
    scripts: List[List[str]] = Field(description="Nmap Scripting engine output")

nmap_parser = PydanticOutputParser(
    pydantic_object=NmapOutputFormat)