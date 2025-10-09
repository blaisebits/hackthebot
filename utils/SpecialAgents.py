import sys
import importlib.util
from pathlib import Path
from langgraph.graph.state import CompiledStateGraph

class SpecialAgent:
    def __init__(self, name:str, graph:CompiledStateGraph, mapping:[str], description:str):
        self.name:str = name
        self.graph:CompiledStateGraph = graph
        self.mapping:[str] = mapping
        self.description:str = description

class SpecialAgentLoader:
    """
    Automates loadings Special Agents from the /specialagents directory.
    Can use the `load_agents()` method to reload agents from disk.
    Can use the `get_agents()` method to return a dict of the agents.
    """
    def __init__(self):
        self.agents_dir = Path.joinpath(Path(__file__).parent, "..","specialagents")
        self.agents: dict[str,SpecialAgent] = {}
        self.load_agents()

    def _load_agent(self, agent_path):
        module_path = agent_path / "agents.py"
        if not module_path.exists():
            print("Module Path doesn't exist")
            return
        try:
            spec = importlib.util.spec_from_file_location(f"{__package__}.{agent_path.name}", module_path)
            module = importlib.util.module_from_spec(spec)

            # Add module directory to Python path if it's not already there
            if str(agent_path.parent) not in sys.path:
                sys.path.insert(0, str(agent_path.parent))

            spec.loader.exec_module(module)

            if hasattr(module, "AGENT_MAPPING"):
                for k,v in module.AGENT_MAPPING.items():
                    self.agents[k] = SpecialAgent(
                        name=k,
                        graph=module.AGENT_MAPPING[k]["graph"],
                        mapping=module.AGENT_MAPPING[k]["agent_mapping"],
                        description=module.AGENT_MAPPING[k]["description"]
                    )

        except Exception as e:
            print(f"Exception: {e}")
            print(f"Failed to load module: {agent_path.name}")
            raise

    def load_agents(self):
        for agent in self.agents_dir.iterdir():
            print(f"Loading agent: {agent.name}")
            if not agent.is_dir():
                continue
            self._load_agent(agent)
        print(f"Loaded Agents:{self.agents.keys()}")

    def get_agents(self):
        return self.agents

    def agent_prompt_data(self):
        data = ""
        for agent in self.agents.keys():
            data += f"* {agent}: {self.agents[agent].description}\n"
        return data


if __name__ == "__main__":
    test = SpecialAgentLoader()
    print(test.agents_dir)
    test.load_agents()
