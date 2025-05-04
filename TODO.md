# TODO List!
## Stinger
* [x] Expand `Task` structure to capture the out of tools or answers to questions
* [x] Adjust task list prompt to leave the answer fields blank on generation, or at least the answer.
* 

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
* [ ] investigate host table being purged, probably done during PFC
  *  https://smith.langchain.com/public/1bca3a82-c6d7-412c-8da2-eb584cc6e3ad/r

## Overall
* [ ] Check tasking data for potential answers before tool calls.
* [ ] Move `OutputFormatters` to a yaml file for dynamic generation.


# Potential future issues
* Handling for multi-system CTFs
* 