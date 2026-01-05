# TODO List!
## Server Management
* [ ] Configure all agents to use file handling from the docker volume 'hackthebot'
* [ ] RoboPages - Let the server handle launching and running
* [ ] DNS server - something to allow ALLLLL docker containers to use for custom DNS entries
  * [ ] Docker container management could probably handle this [Docker DNS](https://docs.docker.com/engine/network/#dns-services)
* [ ] Mythic C2 - Managing Mythic C2
* [ ] Docker Compose to handle services??
  * [ ] Robopages
  * [ ] DNS Server
  * [ ] MCP speciality tools

## General
* [ ] Modify appending `Host` to context with JSON Stringify to cut down on formatting bs
* [x] Upon validation, append the verdicts to the corresponding entry in the state Host dict

## Stinger
* [x] Expand `Task` structure to capture the out of tools or answers to questions
* [x] Adjust task list prompt to leave the answer fields blank on generation, or at least the answer.

## Exploit
### Validator
* [ ] Update logic to test initial access payload to generate the answer and reason fields.

## Recon
* [x] Add `validation` node/graph to validate if the task we completed correctly.
* [x] Add pre-validation loop to check for answers in host object
  * [x] Update host data merging
* [x] Update PreFlightCheck when task switching, check hunting for loop on line 54


## Enum
* [x] Copy additional AI logging messages from ReconAgent to EnumAgent
* [x] Add `validation` node/graph to validate if the task we completed correctly.
* [x] Add pre-validation loop to check for answers in host object
  * [x] Update host data merging
* [x] Update PreFlightCheck when task switching, check hunting for loop on line 54
* [x] investigate host table being purged, probably done during PFC
  *  https://smith.langchain.com/public/1bca3a82-c6d7-412c-8da2-eb584cc6e3ad/r

## Exploit
* investigate langchain deepagent and TodoMiddleware

## Overall
* [ ] Change handling of state table: State is passed by reference, will need place holders for returnable values and not edit the state object directly.
  * [ ] Recon / Enum Agents
  * [ ] Exploit / Agent

### StingerState Mutation Locations
#### StingerAgent.py
- [ ] Line 90: `state["current_task"] = index`
- [ ] Line 154: `state["messages"] = add_messages(...)` (test code)
- [ ] Line 155: `state["context"] = "..."` (test code)

#### EnumAgent.py
- [ ] Line 35: `state["current_task"] = get_new_task(...)`
- [ ] Line 48: `state["current_task"] = get_new_task(...)`
- [ ] Line 55: `state["tasks"][...]["status"] = "working"`
- [ ] Line 69: `state["hosts"][...] = target_host`
- [ ] Line 70: `state["tasks"][...]["preflightcheck"] = True`
- [ ] Line 91: `state["tasks"][...]["tool"].append(...)`
- [ ] Line 134: `state["messages"] = add_messages(...)`
- [ ] Line 136: `state["tasks"][...]["output"].append(output)`
- [ ] Line 150: `state["tasks"][...]["preflightcheck"] = True`
- [ ] Line 169: `state["tasks"][...]["status"] = "validated"`
- [ ] Line 170: `state["tasks"][...]["verdict"] = response`
- [ ] Line 173: `state["hosts"][...]["verdicts"].append(response)`

#### ExploitAgent.py
- [ ] Line 67: `state["current_task"] = get_new_task(...)`
- [ ] Line 83: `state["hosts"][...]["initial_access_exploit"].append(iae)`
- [ ] Line 85: `state["tasks"][...]["status"] = "validated"`
- [ ] Line 101: `state["current_task"] = get_new_task(...)`
- [ ] Line 108: `state["tasks"][...]["status"] = "working"`
- [ ] Line 124: `state["hosts"][...] = target_host`
- [ ] Line 125: `state["tasks"][...]["preflightcheck"] = True`
- [ ] Line 158: `state["tasks"][...]["output"].append(exploit_task)`
- [ ] Line 172: `state["tasks"][...]["preflightcheck"] = True`
- [ ] Line 185: `state["tasks"][...]["status"] = "validated"`
- [ ] Line 190: `state["tasks"][...]["verdict"] = TaskAnswer(...)`
- [ ] Line 300: `state["tasks"][...]["steps"][...]["status"] = "working"`
- [ ] Line 301: `state["tasks"][...]["steps"][...]["scratchpad"] = scratchpad`
- [ ] Line 397: `state["tasks"][...]["steps"] = output_steps`
- [ ] Line 403: `state["tasks"][...]["status"] = new_status`
- [ ] Line 404: `state["tasks"][...]["initial_access_exploit"] = ...`
- [ ] Line 406: `state["tasks"][...]["steps"][-1]["status"] = "validated"`
- [ ] Line 408: `state["tasks"][...]["status"] = "failed"`

#### BrowserAgent/agents.py
- [ ] Line 27: `state["persistent_tools"][...] = {...}`
- [ ] Line 30: `state["persistent_tools"][...] = {...}`
* [ ] Check tasking data for potential answers before tool calls.
* [ ] Move `OutputFormatters` to a yaml file for dynamic generation.
* [ ] Create pydantic BaseModel schemas for use with tool calls to avoid TypedDict missing

# Potential Future components
* Really sick React UI thingy: [ReactFlow](https://reactflow.dev/)
* Actually learn async: [Async Concepts](https://docs.python.org/3/howto/a-conceptual-overview-of-asyncio.html)

# Potential future issues
* Handling for multi-system CTFs
