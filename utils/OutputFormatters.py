from typing import Dict, List
from pydantic import BaseModel, Field
from utils.States import Port

#this is used just for validating tasks
class TaskAnswer(BaseModel):
    """Structured output for validator to check if tasks are completed."""
    question: str = Field(description="The question being asked.")
    answer: str = Field(description="Answer to the question.")

class NmapOutputFormat(BaseModel):
    """Nmap structured output format"""
    ip_address: str = Field(description="The host ip address")
    hostname: List[str] = Field(description="The target DNS hostname")
    ports: Dict[str, Port] = Field(description="Maps the port number and protocol (ie. `80/tcp`) to the states, services, versions, cpe, and scripts output.")

# class GoBusterOutputFormat(BaseModel):
#     """GoBuster structured output format"""
#     target: str = Field(description="Target scanned")
#     ip_address: str = Field(description="The host ip address")
#     hostname: str = Field(description="The target DNS hostname")
#     port: str = Field("Maps the port number and protocol (ie. `80/tcp`) to the tool output")
#     output: List[str] = Field(description="List of discovered directories")

class StandardOutputFormat(BaseModel):
    """Default format for non-specific tool output"""
    target: str = Field(description="Target scanned")
    ip_address: str = Field(description="The host ip address")
    hostname: str = Field(description="The target DNS hostname")
    port: str = Field("Maps the port number and protocol (ie. `80/tcp`) to the tool output")
    output: List[str] = Field(description="Tooling output")

tool_parsers = [
    NmapOutputFormat,
    # GoBusterOutputFormat,
    StandardOutputFormat
]