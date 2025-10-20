# HackTheBot
This is a fun little project to learn LangChain/Graph. The goal will be to solve HackTheBox challenges. Trust none of this code, it lies. 🍰

The end goal will be to have Stinger, the supervising agents, create and assign tasks to the four primary agents; Recon, Enum, Exploit, and PostEx.

Eventually sub agents will be added to handle specialized task i.e. windows priv escalation, web exploitation, Entra ID recon, etc...

This AI agent currently only supports **Anthropic's API**. Other models will be added in the future.

# Setup
This code base can in theory run on Windows, but is designed for use on linux given some the networking features required for Docker.

## Get the code
First, make sure you have Poetry setup on your system, then you can git clone or download a zip of the code base.

```commandline
git clone https://github.com/blaisebits/hackthebot.git
cd hackthebot
poetry install 
```

This will get the virtual env setup, but interactions are currently limited to use with LangGraph studio, see below. 


## ENV file
Copy of the example env file before making changes

```commandline
cp .env.example .env
```

Most of the placeholder variables are already in place. You will only need to set the `ANTHROPIC_API_KEY` variable but you should also set the `LANGSMITH_API_KEY` since interactions are currently limited to using the LangGraph Studio, see below for explanation.

## Robopages
HackTheBot uses [Robopages-cli](https://github.com/dreadnode/robopages-cli/) server and the accompanying [Robopages](https://github.com/dreadnode/robopages/) yaml files for executing tools in docker.

The version of the pages used are customized to point to specific directories in the project folder.

To start the server as a docker container, run the following from inside the project folder.

```commandline
cd robopages
./robopages-server.sh
```

You can also use the `robopages-cli.sh` script to run all the other commands you might need.

## LangGraph Studio Integration
Follow the [LangGraph CLI Install](https://langchain-ai.github.io/langgraph/cloud/reference/cli/) procedure as you'll need this to interact with the LangGraph Studio.

Once installed you can run the following command to link your locally running instance.

```commandline
langgraph dev --config ./StudioConfigs/langgraph-studio.json
```

# Putting it all together
So to run HackTheBot, you'll need to make sure the RoboPages server is online, then execute the langgraph cli command.

Terminal 1
```commandline
cd robopages
./robopages-server.sh
```

Terminal2
```commandline
langgraph dev --config ./StudioConfigs/langgraph-studio.json
```

This will launch a web browser to access LangGraph Studio, you can use the following test data as an example for the TryHackMe [RootMe](https://tryhackme.com/room/rrootme) room.

Make sure and update the target IP Address in the context field after you launch the room target.

```json
{
  "messages": [
    {
      "content": "* Scan the target, how many ports are open?\n* What version of Apache is running?\n* What service is running on port 22?\n* Use GoBuster to find hidden directories. What is the hidden directory?\n* Crawl discovered directories. What URLS have upload forms?\n* Get a remote code execution from a web shell.",
      "type": "human"
    }
  ],
  "hosts": {},
  "context": "Target machine IP Address is 10.10.218.240",
  "current_task": -1,
  "next": ""
}
```
