# Persistent Browser Agent

A robust, stateful browser automation agent built for LangGraph applications that maintains browser sessions across multiple graph node executions. This agent uses Playwright through Microsoft's MCP (Model Context Protocol) server to provide persistent browser automation capabilities.

## Features

- **Persistent Browser Sessions**: Maintains browser state across multiple task executions
- **Cross-Node Compatibility**: Works seamlessly with LangGraph's node-based execution model
- **Conversation Memory**: Preserves conversation history between tasks for contextual awareness
- **Multi-Session Support**: Handles multiple concurrent browser sessions with unique session IDs
- **Auto-Recovery**: Automatically initializes browser sessions when needed
- **Docker Integration**: Uses containerized Playwright for consistent, isolated browser environments
- **Resource Management**: Proper cleanup of Docker containers and browser sessions

## Architecture

### Core Components

1. **PersistentBrowserAgent**: Main agent class that handles browser automation tasks
2. **Module-Level Session Storage**: Persistent state management across different agent instances
3. **Docker Container Management**: Automated Playwright container lifecycle management
4. **MCP Integration**: Communication with Playwright server via Model Context Protocol

### Session Persistence Model

```
Graph Node 1 → PersistentBrowserAgent("session_1") → Browser Container
     ↓
Graph Node 2 → PersistentBrowserAgent("session_1") → Same Browser Container
     ↓                                                (maintains state)
Graph Node 3 → PersistentBrowserAgent("session_1") → Same Browser Container
     ↓
Cleanup Node → agent.close_browser_session() → Container Cleanup
```

## Prerequisites

### Required Dependencies

```bash
# Core dependencies
pip install langchain-mcp-adapters
pip install langgraph
pip install docker
pip install python-dotenv

# LangChain and Anthropic
pip install langchain
pip install langchain-anthropic
```

### Docker Requirements

- Docker must be installed and running
- Access to pull the Microsoft Playwright MCP image:
  ```bash
  docker pull mcr.microsoft.com/playwright/mcp:v0.0.32
  ```

### Environment Setup

Create a `.env` file with your Anthropic API key:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Installation

1. **Clone or download** the `PersistentBrowserAgent` code
2. **Install dependencies** using pip or poetry
3. **Ensure Docker is running** and accessible
4. **Set up environment variables** in `.env` file

## Usage

### Basic Usage

```python
from persistent_browser_agent import PersistentBrowserAgent
import asyncio

async def simple_example():
    # Create agent with session ID
    agent = PersistentBrowserAgent("my_session")
    
    # Execute tasks - browser session auto-initializes
    result1 = await agent.execute_task("Navigate to https://example.com")
    result2 = await agent.execute_task("Describe what you see on the page")
    
    # Clean up when done
    await agent.close_browser_session()

# Run the example
asyncio.run(simple_example())
```

### LangGraph Integration

```python
from langgraph import StateGraph
from persistent_browser_agent import PersistentBrowserAgent

# Define your graph state
class GraphState(TypedDict):
    task_results: List[str]
    session_id: str

# Navigation node
async def navigation_node(state: GraphState):
    agent = PersistentBrowserAgent(state["session_id"])
    result = await agent.execute_task("Navigate to the target website")
    return {
        "task_results": state["task_results"] + [str(result)],
        "session_id": state["session_id"]
    }

# Search node (uses same browser session)
async def search_node(state: GraphState):
    agent = PersistentBrowserAgent(state["session_id"])
    result = await agent.execute_task("Search for products")
    return {
        "task_results": state["task_results"] + [str(result)],
        "session_id": state["session_id"]
    }

# Cleanup node
async def cleanup_node(state: GraphState):
    agent = PersistentBrowserAgent(state["session_id"])
    await agent.close_browser_session()
    return state

# Build graph
graph = StateGraph(GraphState)
graph.add_node("navigate", navigation_node)
graph.add_node("search", search_node)
graph.add_node("cleanup", cleanup_node)
# ... add edges and compile
```

### Multiple Sessions

```python
async def multi_session_example():
    # Different sessions for parallel workflows
    agent_a = PersistentBrowserAgent("session_a")
    agent_b = PersistentBrowserAgent("session_b")
    
    # These run in separate browser instances
    await agent_a.execute_task("Navigate to site A")
    await agent_b.execute_task("Navigate to site B")
    
    # Check active sessions
    print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}")
    
    # Clean up specific sessions
    await agent_a.close_browser_session()
    await agent_b.close_browser_session()
    
    # Or clean up all at once
    # await PersistentBrowserAgent.close_all_sessions()
```

## API Reference

### PersistentBrowserAgent

#### Constructor
```python
PersistentBrowserAgent(session_id: str = "default")
```
- **session_id**: Unique identifier for the browser session (default: "default")

#### Methods

##### `async start_browser_session()`
Explicitly initialize the browser container and agent session. Called automatically by `execute_task()` if not already started.

**Returns**: None

**Raises**: 
- `TimeoutError`: If container fails to start within timeout period

##### `async execute_task(task_content: str)`
Execute a browser automation task using the persistent agent.

**Parameters**:
- `task_content`: Natural language description of the task to perform

**Returns**: LangGraph agent response state containing:
- `messages`: Conversation history with the agent
- `usage_metadata`: Token usage information
- Additional response metadata

**Raises**:
- `RuntimeError`: If browser session initialization fails

##### `async close_browser_session()`
Clean up the browser session, stop the Docker container, and remove session from storage.

**Returns**: None

#### Static Methods

##### `get_active_sessions() -> List[str]`
Get list of currently active session IDs.

**Returns**: List of active session ID strings

##### `async close_all_sessions()`
Close all active browser sessions and clean up resources.

**Returns**: None

#### Context Manager Support
```python
async with PersistentBrowserAgent("session_id") as agent:
    result = await agent.execute_task("Browse to website")
    # Automatic cleanup on exit
```

## Configuration

### Docker Container Settings

The agent uses these default Docker settings:
- **Image**: `mcr.microsoft.com/playwright/mcp:v0.0.32`
- **Port Range**: 10000-10999 (randomly assigned)
- **Volume**: `hackthebot:/data` (for session/trace storage)
- **Capabilities**: Vision support enabled
- **Auto-remove**: Container automatically removed on stop

### Playwright Features

Enabled features:
- **Session Saving**: Browser state persists between tasks
- **Trace Recording**: Full interaction traces saved to volume
- **Vision Capabilities**: Screenshot and visual analysis support
- **Full Browser API**: Complete Playwright automation capabilities

## Error Handling

### Common Issues and Solutions

#### Container Startup Timeout
```python
# Increase timeout if needed
TimeoutError: Container failed to start within timeout period
```
**Solution**: Check Docker daemon status and network connectivity

#### Port Conflicts
If you encounter port binding errors, the agent automatically retries with different random ports in the 10000-10999 range.

#### Session Cleanup Errors
```python
# Always ensure proper cleanup
try:
    await agent.execute_task("Some task")
finally:
    await agent.close_browser_session()
```

#### MCP Connection Issues
Ensure the Docker container is fully started before attempting MCP connections. The agent waits for "Listening on" message in container logs.

## Best Practices

### Session Management

1. **Use Descriptive Session IDs**: Use meaningful names for different workflows
```python
agent = PersistentBrowserAgent("user_shopping_session")
```

2. **Always Clean Up**: Ensure sessions are closed when workflows complete
```python
try:
    # ... workflow tasks ...
finally:
    await agent.close_browser_session()
```

3. **Monitor Active Sessions**: Use utility methods to track resource usage
```python
print(f"Active sessions: {PersistentBrowserAgent.get_active_sessions()}")
```

### Task Design

1. **Be Specific**: Provide clear, actionable task descriptions
```python
# Good
await agent.execute_task("Click the 'Sign In' button in the top navigation")

# Less effective
await agent.execute_task("Sign in")
```

2. **Leverage Context**: The agent remembers previous actions in the session
```python
await agent.execute_task("Navigate to the shopping cart")
await agent.execute_task("Remove the first item from the cart")  # Knows which cart
```

3. **Use Vision Capabilities**: Take advantage of Playwright's visual features
```python
await agent.execute_task("Take a screenshot of the current page state")
await agent.execute_task("Describe what you see in the main content area")
```

### Performance Considerations

1. **Reuse Sessions**: Don't create new sessions unnecessarily
2. **Batch Related Tasks**: Group related browser actions in the same session
3. **Clean Up Promptly**: Close sessions when workflows complete to free resources

## Troubleshooting

### Debug Information

Enable debug output by checking container logs:
```python
# Access container logs for debugging
state = agent._get_session_state()
if state['container']:
    print(state['container'].logs().decode("utf-8"))
```

### Resource Monitoring

Check system resources:
```python
# Monitor active sessions
active = PersistentBrowserAgent.get_active_sessions()
print(f"Active sessions: {len(active)} - {active}")

# Check Docker containers
import docker
client = docker.from_env()
containers = client.containers.list(filters={"ancestor": "mcr.microsoft.com/playwright/mcp:v0.0.32"})
print(f"Active containers: {len(containers)}")
```

## Examples

See the included test function for a complete example of multi-node graph execution simulation.

## License

This project uses the Microsoft Playwright MCP server image and follows the associated licensing terms.
