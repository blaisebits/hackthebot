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

## Overall
* [ ] Check tasking data for potential answers before tool calls.
* [ ] Move `OutputFormatters` to a yaml file for dynamic generation.


# Potential future issues
* Handling for multi-system CTFs
