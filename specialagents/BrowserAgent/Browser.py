import asyncio
import string
from datetime import datetime, timedelta
from random import choice, randint

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent


import docker

# Module-level session storage
_BROWSER_SESSIONS = {}

class PersistentBrowserAgent:
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id

    def _get_session_state(self):
        """Get or create session state for this session_id"""
        if self.session_id not in _BROWSER_SESSIONS:
            _BROWSER_SESSIONS[self.session_id] = {
                'docker_socket': docker.from_env(),
                'container': None,
                'container_name': None,
                'container_port': None,
                'client': None,
                'session': None,
                'agent': None,
                '_session_context': None,
                '_message_history': {"messages": []}
            }
        return _BROWSER_SESSIONS[self.session_id]

    async def start_browser_session(self):
        """Initialize the browser container and agent session"""
        state = self._get_session_state()

        if state['container'] is not None:
            print(f"Browser session '{state['container_name']}' already active")
            return

        # Generate unique container name and port
        state['container_name'] = "browser_" + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(5))
        state['container_port'] = randint(10000, 10999)

        print(f"Starting browser container: {state['container_name']} on port {state['container_port']}")

        # Start Docker container
        state['container'] = state['docker_socket'].containers.run(
            image="mcr.microsoft.com/playwright/mcp:v0.0.32",
            name=state['container_name'],
            detach=True,
            auto_remove=True,
            ports={"8931": state['container_port']},
            volumes=["hackthebot:/data"],
            command="--port 8931 --caps=vision --output-dir /data/browser --save-session --save-trace"
        )

        # Wait for container to be ready
        time = datetime.now()
        td = timedelta(seconds=10)
        timeout = time + td
        while datetime.now() < timeout:
            if "Listening on" in state['container'].logs().decode("utf-8"):
                break
        else:
            raise TimeoutError("Container failed to start within timeout period")

        # Initialize MCP client
        state['client'] = MultiServerMCPClient({
            "browser": {
                "url": f"http://localhost:{state['container_port']}/mcp",
                "transport": "streamable_http",
            }
        })

        # Create persistent session
        state['_session_context'] = state['client'].session("browser")
        state['session'] = await state['_session_context'].__aenter__()

        # Load tools and create agent
        tools = await load_mcp_tools(state['session'])
        state['agent'] = create_react_agent(
            "anthropic:claude-3-5-sonnet-latest",
            tools
        )

        print("Browser session initialized successfully")

    async def execute_task(self, task_content: str):
        """Execute a task using the persistent browser agent"""
        state = self._get_session_state()

        # Auto-initialize if not already started
        if state['agent'] is None:
            await self.start_browser_session()

        query = {"messages": state['_message_history']["messages"] + [{"role": "user", "content": task_content}]}
        response_state = await state['agent'].ainvoke(query)
        state['_message_history'] = response_state
        return response_state

    async def close_browser_session(self):
        """Clean up the browser session and container"""
        if self.session_id not in _BROWSER_SESSIONS:
            return

        state = _BROWSER_SESSIONS[self.session_id]

        if state['_session_context'] is not None:
            try:
                await state['_session_context'].__aexit__(None, None, None)
            except Exception as e:
                print(f"Error closing session: {e}")
            finally:
                state['_session_context'] = None
                state['session'] = None
                state['agent'] = None

        if state['container'] is not None:
            try:
                state['container'].stop()
                print(f"Stopped container: {state['container_name']}")
            except Exception as e:
                print(f"Error stopping container: {e}")
            finally:
                state['container'] = None
                state['container_name'] = None
                state['container_port'] = None

        if state['client'] is not None:
            state['client'] = None

        # Remove session from module storage
        del _BROWSER_SESSIONS[self.session_id]
        print(f"Session '{self.session_id}' removed from storage")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_browser_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_browser_session()

    @staticmethod
    def get_active_sessions():
        """Get list of currently active session IDs"""
        return list(_BROWSER_SESSIONS.keys())

    @staticmethod
    async def close_all_sessions():
        """Close all active browser sessions"""
        session_ids = list(_BROWSER_SESSIONS.keys())
        for session_id in session_ids:
            agent = PersistentBrowserAgent(session_id)
            await agent.close_browser_session()


async def simulate_graph_node_execution():
    """Simulate how this would be used in different Langgraph nodes"""
    print("=== Simulating Graph Node Execution ===\n")

    # Simulate Node 1: Navigation
    print("--- Graph Node 1: Navigation ---")
    agent1 = PersistentBrowserAgent("my_session")
    result1 = await agent1.execute_task("Browse to https://www.automationexercise.com")
    print(f"Node 1 completed: ✓")
    print(f"Results: {result1["messages"][-1].content}")
    print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}\n")

    # Simulate Node 2: Search (different agent instance, same session)
    print("--- Graph Node 2: Search ---")
    agent2 = PersistentBrowserAgent("my_session")  # Same session_id
    result2 = await agent2.execute_task("Search for mens jeans for sale")
    print(f"Node 2 completed: ✓")
    print(f"Results: {result2["messages"][-1].content}")
    print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}\n")

    # Simulate Node 3: Product listing
    print("--- Graph Node 3: Product Listing ---")
    agent3 = PersistentBrowserAgent("my_session")  # Same session_id
    result3 = await agent3.execute_task("List the types of jeans for sale and their prices.")
    print(f"Node 3 completed: ✓")
    print(f"Results: {result3["messages"][-1].content}")
    print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}\n")

    # Simulate cleanup node
    print("--- Graph Node 4: Cleanup ---")
    agent4 = PersistentBrowserAgent("my_session") # Same session_id
    await agent4.close_browser_session()
    print(f"Cleanup completed: ✓")
    print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}\n")

if __name__ == "__main__":
    print("Testing Persistent Browser Agent with Module-Level State")
    print("=" * 60)

    asyncio.run(simulate_graph_node_execution())


# Example calling from parent graph.
# # Node 1 - Navigation
# async def navigation_node(state):
#     agent = PersistentBrowserAgent("user_session")
#     result = await agent.execute_task("Navigate to website")
#     return {"nav_result": result}
#
# # Node 2 - Search (later in graph)
# async def search_node(state):
#     agent = PersistentBrowserAgent("user_session")  # Same session!
#     result = await agent.execute_task("Search for products")
#     return {"search_result": result}
#
# # Final cleanup
# async def cleanup_node(state):
#     agent = PersistentBrowserAgent("user_session")
#     await agent.close_browser_session()
#     return {"cleanup": "complete"}