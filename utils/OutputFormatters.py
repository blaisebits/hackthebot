from typing import Dict, List, Literal
from pydantic import BaseModel, Field
from utils.States import Port

class SpecialAgentCaller(BaseModel):
    name:str = Field(description="Name of the special agent to pass execution")

class TaskAnswer(BaseModel):
    """Structured output for validator to check if tasks are completed."""
    question: str = Field(description="The question being asked.")
    answer: str = Field(description="Answer to the question.")
    reason: str = Field(description="The logic used to provide the answer.")

class TaskBasicInfo(BaseModel):
    task: str = Field(description="The task to be executed")
    agent: Literal["Recon", "Enum", "Exploit", "PostEx"] = Field(description="The agent that will handle the task.")
    target_ip: str = Field(description="The target host IP address.")

class TaskBasicInfoList(BaseModel):
    tasks: List[TaskBasicInfo] = Field(description="A list of the tasks with basic information.")

class ExploitStep(BaseModel):
    steps: List[str] = Field(description="A list of steps to execute, in order, to exploit a target for remote code execution.")

class ExploitSuggestions(BaseModel):
    tasks: List[str] = Field(description="A list of exploitation methods that could potentially be used to exploit the target for remote code execution.")

class ExploitStepStatus(BaseModel):
    status: Literal["validated", "failed"] = Field(description="The status of the Exploit Step. Validated if successful, failed if unsuccessful")
    revision: str = Field(description="The revised version of the task adjusted for previous errors. Leave Blank if status is validated.")

############################################################
##### TOOL SPECIFIC OUTPUT FORMATTERS FOR SPECIAL CASES ####
############################################################

class NmapOutputFormat(BaseModel):
    """Nmap structured output format"""
    ip_address: str = Field(description="The host ip address")
    hostname: List[str] = Field(description="The target DNS hostname")
    ports: Dict[str, Port] = Field(description="Maps the port number and protocol (ie. `80/tcp`) to the states, services, versions, cpe, and scripts output.")

class StandardOutputFormat(BaseModel):
    """Default format for non-specific tool output"""
    target: str = Field(description="Target scanned")
    ip_address: str = Field(description="The host ip address")
    hostname: str = Field(description="The target DNS hostname")
    port: str = Field("Maps the port number and protocol (ie. `80/tcp`) to the tool output")
    output: List[str] = Field(description="Tooling output")

tool_parsers = [
    NmapOutputFormat,
    StandardOutputFormat
]