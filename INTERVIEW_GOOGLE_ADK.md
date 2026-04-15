# Google ADK (Agent Development Kit) - 30 Interview Questions & Answers

---

## ADK Core Concepts (Q1-Q5)

### Q1: What is Google ADK (Agent Development Kit) and what problem does it solve?
**Answer:** Google ADK (Agent Development Kit) is an open-source, code-first Python (and TypeScript/Go/Java) framework for building, evaluating, and deploying sophisticated AI agents and multi-agent systems. It solves the problem of fragmented agent development by providing a unified framework that handles agent orchestration, tool integration, session/state management, and deployment. While optimized for Gemini and the Google Cloud ecosystem, ADK is model-agnostic (supports OpenAI, Claude, Mistral via LiteLLM) and deployment-agnostic (Cloud Run, Vertex AI Agent Engine, GKE, or self-hosted). Unlike ad-hoc agent scripts, ADK provides structured primitives -- `Agent`, `Runner`, `Session`, `Tools`, and `Events` -- that compose into production-grade agentic applications with built-in evaluation, streaming, and state persistence. Install via `pip install google-adk`.

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[],
)
```

---

### Q2: Explain the `LlmAgent` class and its key parameters: `model`, `instruction`, `output_key`, `description`, and `tools`.
**Answer:** `LlmAgent` (aliased as `Agent`) is the primary agent class that uses a Large Language Model as its reasoning engine. Its key parameters are:

- **`name`** (str): Unique identifier for the agent within the agent tree. Used in `transfer_to_agent` calls and event attribution.
- **`model`** (str or connector object): The LLM to use. For Gemini: `"gemini-2.0-flash"` or `"gemini-1.5-pro"`. For other providers, pass a `LiteLlm("openai/gpt-4o")` connector object.
- **`instruction`** (str or callable): System prompt guiding the agent. Supports state templating with `{key}` syntax, e.g., `"Help the user. Their name is {user:name}."` The framework resolves state references at runtime. Can also be a callable `InstructionProvider` for dynamic instructions.
- **`output_key`** (str, optional): When set, the agent's final text response is automatically saved to `session.state[output_key]`. This is the primary mechanism for passing data between agents in sequential pipelines.
- **`description`** (str): A natural-language description of the agent's capabilities. Used by parent LLM agents to decide when to delegate/transfer to this agent.
- **`tools`** (list): List of `FunctionTool`, `AgentTool`, `McpToolset`, or built-in tools the agent can invoke.
- **`sub_agents`** (list): Child agents for hierarchical composition or LLM-driven delegation.

```python
agent = LlmAgent(
    name="researcher",
    model="gemini-2.0-flash",
    instruction="Research the topic: {topic}. Summarize findings.",
    description="Researches topics using web search.",
    output_key="research_summary",
    tools=[google_search_tool],
    sub_agents=[detail_agent],
)
```

---

### Q3: How does ADK differ from LangChain, LangGraph, and CrewAI?
**Answer:** ADK differs from these frameworks in several key ways:

| Aspect | ADK | LangChain/LangGraph | CrewAI |
|--------|-----|---------------------|--------|
| **Philosophy** | Code-first, modular agents as composable units | Chain-of-thought composition (LangChain) / Graph-based state machines (LangGraph) | Role-based crew metaphor |
| **Multi-agent** | Native hierarchical sub_agents with SequentialAgent, ParallelAgent, LoopAgent, and LLM-driven transfer_to_agent | LangGraph supports multi-actor graphs; LangChain is single-chain focused | Native crew/task delegation |
| **State** | Event-sourced state with prefix scoping (app:, user:, temp:) and pluggable SessionService (InMemory, Database, VertexAI) | LangGraph has channel-based state; LangChain uses memory classes | Shared crew memory |
| **Model support** | Gemini-native + LiteLLM adapter for 100+ models | Broad model support via provider classes | Primarily OpenAI-focused |
| **Deployment** | First-class deploy to Cloud Run, Vertex AI Agent Engine, GKE with `adk deploy` CLI | Self-managed deployment | Self-managed |
| **Evaluation** | Built-in eval framework with trajectory scoring, response matching, hallucination checks | LangSmith for tracing/eval (separate product) | No built-in eval |
| **Protocol** | Native A2A (Agent-to-Agent) protocol support for cross-system agent communication | No equivalent | No equivalent |

ADK is best when you want tight Google Cloud integration, built-in multi-agent patterns, and a batteries-included framework from agent creation to production deployment.

---

### Q4: What is the Event system in ADK and what types of Events exist?
**Answer:** Events are the fundamental unit of communication in ADK, representing everything that happens during a session -- user messages, agent responses, tool invocations, and state changes. Events form the chronological conversation history stored in the session. Each Event has:

- **`author`**: Who produced the event (agent name, "user", or "system").
- **`content`**: The message content with `parts` (text, function calls, function responses).
- **`actions`**: An `EventActions` object that can carry `state_delta` (state changes), `transfer_to_agent` (delegation target), `escalate` (break out of loops/return to parent), and `skip_summarization`.
- **`invocation_id`**: Links the event to a specific invocation.
- **`partial`**: Boolean flag for streaming -- partial events are intermediate chunks not persisted to session history.

The Runner yields events as an async generator, enabling real-time streaming:

```python
from google.adk.runners import Runner
from google.genai import types

runner = Runner(agent=my_agent, session_service=session_service)
user_msg = types.Content(role="user", parts=[types.Part.from_text("Hello")])

async for event in runner.run_async(user_id="u1", session_id="s1", new_message=user_msg):
    if event.content and event.content.parts:
        print(f"[{event.author}]: {event.content.parts[0].text}")
    if event.actions and event.actions.state_delta:
        print(f"State changed: {event.actions.state_delta}")
```

---

### Q5: What is `output_key` and how does it enable inter-agent communication?
**Answer:** `output_key` is an optional parameter on `LlmAgent` that automatically persists the agent's final text response into `session.state[output_key]`. This is the primary mechanism for data flow between agents in sequential pipelines. When the Runner processes the agent's response event, it creates a `state_delta` entry mapping the `output_key` to the response text, which gets persisted via `append_event`.

Downstream agents then reference this state value using `{key}` template syntax in their instructions. This decouples agents -- they communicate through shared state rather than direct invocation:

```python
# Agent A writes to state
capital_finder = LlmAgent(
    name="CapitalFinder",
    model="gemini-2.0-flash",
    instruction="What is the capital of {country}? Reply with just the city name.",
    output_key="capital_city",  # Response saved to state["capital_city"]
)

# Agent B reads from state
travel_guide = LlmAgent(
    name="TravelGuide",
    model="gemini-2.0-flash",
    instruction="Write a short travel guide for {capital_city}.",  # Reads state["capital_city"]
    output_key="travel_info",
)

# Sequential pipeline connects them
from google.adk.agents import SequentialAgent
pipeline = SequentialAgent(name="TravelPipeline", sub_agents=[capital_finder, travel_guide])
```

When `CapitalFinder` responds "Paris", it is saved to `state["capital_city"]`. When `TravelGuide` runs next, `{capital_city}` resolves to "Paris" in its instruction.

---

## Agent Types (Q6-Q9)

### Q6: Compare LlmAgent, SequentialAgent, ParallelAgent, and LoopAgent. When do you use each?
**Answer:** ADK provides two categories of agents: LLM Agents (non-deterministic, LLM-driven) and Workflow Agents (deterministic, no LLM for flow control):

| Agent | Type | Behavior | Use Case |
|-------|------|----------|----------|
| **LlmAgent** | LLM | Uses an LLM to reason, plan, select tools, and decide next steps dynamically | Flexible tasks requiring NL understanding, tool selection, delegation |
| **SequentialAgent** | Workflow | Executes sub_agents in strict order, one after another | ETL pipelines, multi-step processing, review chains |
| **ParallelAgent** | Workflow | Executes all sub_agents concurrently | Fan-out data gathering, independent API calls, parallel analysis |
| **LoopAgent** | Workflow | Repeats sub_agents sequentially in a loop until `max_iterations` or `escalate=True` | Iterative refinement, polling, retry logic, critique-revise cycles |

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent

# Parallel: gather data concurrently
gatherer = ParallelAgent(
    name="DataGatherer",
    sub_agents=[weather_agent, news_agent, stock_agent]
)

# Sequential: process in order
pipeline = SequentialAgent(
    name="ReportPipeline",
    sub_agents=[gatherer, summarizer_agent, formatter_agent]
)

# Loop: refine until quality threshold met
refiner = LoopAgent(
    name="QualityLoop",
    max_iterations=5,
    sub_agents=[writer_agent, critic_agent, quality_checker]
)
```

Key distinction: Workflow agents do NOT use an LLM for orchestration decisions -- the flow is hardcoded. The LLM is only used within the child `LlmAgent` instances for their specific tasks.

---

### Q7: How does `LoopAgent` work and how do you break out of a loop using `escalate`?
**Answer:** `LoopAgent` executes its `sub_agents` sequentially in a repeating loop. Each iteration runs all sub_agents in order. The loop terminates when either `max_iterations` is reached, or any sub-agent yields an `Event` with `escalate=True` in its `EventActions`. The escalation mechanism is the programmatic way to signal "we are done" from within the loop.

For LLM-based sub-agents, you instruct the LLM to set escalation. For custom agents, you yield the event directly:

```python
from google.adk.agents import LlmAgent, LoopAgent

# LLM-based checker that decides when to stop
quality_checker = LlmAgent(
    name="QualityChecker",
    model="gemini-2.0-flash",
    instruction="""Review the draft in {draft}.
    If quality is acceptable, respond with 'APPROVED' and set escalate to true.
    If not, provide specific feedback for improvement.""",
    output_key="feedback",
)

# Custom agent approach for programmatic escalation
from google.adk.agents import BaseAgent
from google.adk.events import Event, EventActions

class ThresholdChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        score = ctx.session.state.get("quality_score", 0)
        is_done = score >= 0.9
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            actions=EventActions(escalate=is_done),  # Breaks loop when True
        )

loop = LoopAgent(
    name="RefinementLoop",
    max_iterations=10,
    sub_agents=[writer_agent, quality_checker],  # or ThresholdChecker
)
```

When `escalate=True` is yielded, the LoopAgent stops iteration and returns control to its parent agent.

---

### Q8: How do you create a custom agent by extending `BaseAgent`?
**Answer:** You extend `BaseAgent` and implement the `_run_async_impl` method, which is an async generator that yields `Event` objects. This gives you full control over orchestration logic -- conditional branching, dynamic agent selection, state-based routing, and custom iteration patterns that go beyond the built-in workflow agents.

```python
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

class ConditionalRouter(BaseAgent):
    """Routes to different agents based on session state."""
    analyzer: LlmAgent
    technical_agent: LlmAgent
    general_agent: LlmAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, analyzer, technical_agent, general_agent):
        super().__init__(
            name="ConditionalRouter",
            sub_agents=[analyzer, technical_agent, general_agent],
            analyzer=analyzer,
            technical_agent=technical_agent,
            general_agent=general_agent,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Step 1: Analyze the query
        async for event in self.analyzer.run_async(ctx):
            yield event

        # Step 2: Route based on analysis result
        category = ctx.session.state.get("query_category", "general")
        if category == "technical":
            async for event in self.technical_agent.run_async(ctx):
                yield event
        else:
            async for event in self.general_agent.run_async(ctx):
                yield event
```

Key rules: (1) Always yield events from sub-agents to maintain framework visibility. (2) Use `ctx.session.state` for inter-agent data sharing. (3) Pass all sub-agents to `super().__init__(sub_agents=...)` so ADK knows the agent hierarchy.

---

### Q9: When should you use LLM-driven delegation vs. workflow agents for multi-agent orchestration?
**Answer:** The choice depends on whether the routing logic is dynamic or deterministic:

**Use LLM-driven delegation (LlmAgent with sub_agents)** when:
- The routing decision requires natural language understanding (e.g., "is this a billing question or a technical question?")
- The flow is non-deterministic and depends on user intent
- You want the LLM to choose which specialist agent handles the request
- The agent needs to handle open-ended conversations with dynamic handoffs

```python
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="Route billing questions to BillingAgent, technical issues to TechAgent.",
    sub_agents=[billing_agent, tech_agent],  # LLM generates transfer_to_agent() calls
)
```

**Use workflow agents (Sequential/Parallel/Loop)** when:
- The execution order is fixed and predictable (e.g., "always run validation then processing then notification")
- You want guaranteed execution patterns without LLM variability
- You need parallel fan-out or iterative refinement loops
- Cost/latency matters -- workflow agents do not consume LLM tokens for orchestration

**Combine both** in practice: use a workflow agent as the top-level orchestrator with LLM agents as sub-agents that handle individual steps:

```python
pipeline = SequentialAgent(
    name="Pipeline",
    sub_agents=[
        data_collector,        # LlmAgent with tools
        ParallelAgent(name="Validators", sub_agents=[format_checker, fact_checker]),
        coordinator,           # LlmAgent that delegates dynamically
    ]
)
```

---

## Tools (Q10-Q13)

### Q10: How do you define a plain function as a tool in ADK? What are the conventions?
**Answer:** In ADK, any Python function can become a tool by wrapping it with `FunctionTool` or simply passing it in the agent's `tools` list (ADK auto-wraps plain functions). The LLM uses the function's **name**, **docstring**, and **type-annotated parameters** to decide when and how to call it. This makes clear docstrings and type hints critical.

```python
from google.adk.tools import FunctionTool

def get_weather(city: str, units: str = "celsius") -> dict:
    """Retrieves the current weather for a specified city.

    Args:
        city: The name of the city to get weather for.
        units: Temperature units, either 'celsius' or 'fahrenheit'.

    Returns:
        A dictionary with weather status and temperature.
    """
    # Simulated API call
    weather_data = {
        "london": {"status": "success", "report": "Cloudy, 18C"},
        "paris": {"status": "success", "report": "Sunny, 22C"},
    }
    result = weather_data.get(city.lower())
    if result:
        return result
    return {"status": "error", "error_message": f"City '{city}' not found"}

# Explicit wrapping
weather_tool = FunctionTool(func=get_weather)

# Or pass directly -- ADK auto-wraps
agent = LlmAgent(
    name="WeatherBot",
    model="gemini-2.0-flash",
    instruction="Use the get_weather tool when asked about weather.",
    tools=[get_weather],  # Auto-wrapped to FunctionTool
)
```

Conventions: (1) Use clear, descriptive function names. (2) Write comprehensive docstrings -- the LLM reads them. (3) Type-annotate all parameters. (4) Return dictionaries with status/error fields for robust error handling. (5) Keep tool functions focused on a single action.

---

### Q11: What is `ToolContext` and how do you use it to access session state and control agent flow?
**Answer:** `ToolContext` is a special parameter that ADK automatically injects into your tool function when included in the signature. It provides access to session state, event actions, artifacts, and memory -- enabling tools to read/write state and influence agent behavior. Crucially, do NOT document `tool_context` in the docstring since it is framework-injected and irrelevant to the LLM's tool selection.

```python
from google.adk.tools import ToolContext

def add_to_cart(item_name: str, quantity: int, tool_context: ToolContext) -> dict:
    """Adds an item to the user's shopping cart.

    Args:
        item_name: Name of the item to add.
        quantity: Number of items to add.
    """
    # Read state
    cart = tool_context.state.get("user:cart", [])

    # Modify state (tracked as state_delta, persisted by SessionService)
    cart.append({"item": item_name, "qty": quantity})
    tool_context.state["user:cart"] = cart
    tool_context.state["temp:last_action"] = "add_to_cart"  # Temporary, not persisted

    # Control agent flow
    if len(cart) >= 10:
        tool_context.actions.transfer_to_agent = "checkout_agent"  # Hand off

    return {"status": "success", "cart_size": len(cart)}

def emergency_escalate(issue: str, tool_context: ToolContext) -> dict:
    """Escalates an emergency issue to a human operator."""
    tool_context.actions.escalate = True  # Return control to parent agent
    tool_context.actions.skip_summarization = True  # Skip LLM summary of tool output
    return {"status": "escalated", "issue": issue}
```

Key `ToolContext` attributes:
- **`state`**: Read/write `session.state` (supports all prefixes: `app:`, `user:`, `temp:`, none)
- **`actions.transfer_to_agent`**: Delegate to another agent by name
- **`actions.escalate`**: Signal parent/loop agent to take over
- **`actions.skip_summarization`**: Return tool output directly without LLM summarization
- **`function_call_id`**: Unique ID for this invocation
- **`load_artifact()` / `save_artifact()`**: Read/write binary artifacts
- **`search_memory(query)`**: Query long-term memory service

---

### Q12: What is `AgentTool` and how does it differ from `sub_agents` delegation?
**Answer:** `AgentTool` wraps an agent as a callable tool within another agent's toolset. The parent LLM explicitly calls the wrapped agent like any other tool function, receives its output, and continues its own reasoning. This differs from `sub_agents` delegation where the parent transfers full control to the child agent.

| Aspect | AgentTool | sub_agents (transfer_to_agent) |
|--------|-----------|-------------------------------|
| **Control** | Parent retains control; child runs and returns result | Full control transfers to child; parent pauses |
| **Usage** | Parent calls child as a tool mid-reasoning | Parent generates `transfer_to_agent` and yields control |
| **Return** | Child result goes back to parent as tool response | Child responds directly to user |
| **Best for** | Using a specialist agent for a subtask within a larger flow | Routing entire conversations to specialist agents |

```python
from google.adk.tools.agent_tool import AgentTool

# Create a specialist agent
image_describer = LlmAgent(
    name="ImageDescriber",
    model="gemini-2.0-flash",
    instruction="Describe the given image in detail.",
)

# Wrap it as a tool
image_tool = AgentTool(agent=image_describer)

# Parent agent uses it as a tool (retains control)
content_creator = LlmAgent(
    name="ContentCreator",
    model="gemini-2.0-flash",
    instruction="""Create social media posts.
    When you need image descriptions, use the ImageDescriber tool.
    Incorporate the description into your post.""",
    tools=[image_tool],  # Agent used as a tool
)
```

Use `AgentTool` when the parent needs the child's output to continue its own reasoning. Use `sub_agents` when you want full delegation (e.g., a coordinator handing off to a specialist).

---

### Q13: How do you integrate MCP (Model Context Protocol) tools with ADK agents?
**Answer:** ADK integrates MCP servers via the `McpToolset` class, which discovers tools from an MCP server, converts them to ADK-compatible `BaseTool` instances, and proxies execution calls. It supports both local servers (via `StdioConnectionParams`) and remote servers (via `SseConnectionParams` or `StreamableHTTPConnectionParams`).

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

# Local MCP server (e.g., filesystem server)
local_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
        )
    ),
    tool_filter=["read_file", "list_directory"],  # Optional: expose only specific tools
)

# Remote MCP server (e.g., Google Maps)
remote_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mapstools.googleapis.com/mcp",
        headers={"X-Goog-Api-Key": "YOUR_API_KEY"},
    )
)

# Use in agent
agent = LlmAgent(
    name="FileAssistant",
    model="gemini-2.0-flash",
    instruction="Help users manage files and find locations.",
    tools=[local_toolset, remote_toolset],
)
```

ADK also provides built-in tools that do not require MCP:
- **`google_search`**: Grounding with Google Search results
- **`built_in_code_execution`**: Execute code in a sandboxed environment
- **`VertexAiRagRetrieval`**: RAG against Vertex AI corpus

```python
from google.adk.tools import google_search, built_in_code_execution

agent = LlmAgent(
    name="ResearchAgent",
    model="gemini-2.0-flash",
    instruction="Research and compute answers using search and code execution.",
    tools=[google_search, built_in_code_execution],
)
```

---

## Runner (Q14-Q16)

### Q14: What is the Runner class and what is its lifecycle?
**Answer:** The `Runner` is the execution engine that orchestrates the interaction between the user, agents, sessions, and tools. It manages the complete lifecycle of processing a user message through an agent system. The Runner coordinates four backend services:

1. **Agent**: The root agent (and its sub-agent tree)
2. **SessionService**: Persistence for conversation history and state
3. **ArtifactService**: Storage for binary files/documents (optional)
4. **MemoryService**: Long-term memory across sessions (optional)

**Lifecycle per invocation:**
1. **Session Retrieval**: Runner calls `session_service.get_session()` to load conversation history and state
2. **Message Integration**: User's new message is prepared as a `Content` object
3. **Context Creation**: Runner builds an `InvocationContext` containing the session, agent config, and services
4. **Agent Execution**: Runner calls `agent.run_async(invocation_context)` which returns an async generator of Events
5. **Event Processing**: Runner iterates events, yielding them to the caller for streaming
6. **State Persistence**: For each non-partial event, Runner calls `session_service.append_event(session, event)` to persist state changes and conversation history
7. **Session Update**: The session's `last_update_time` is updated

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    session_service=session_service,
    # artifact_service=...,  # optional
    # memory_service=...,    # optional
)
```

---

### Q15: How do you use `run_async` for event streaming? Show a complete example.
**Answer:** `run_async` is an async generator method that yields `Event` objects as the agent processes a user message. This enables real-time streaming of intermediate results, tool calls, and final responses. You iterate over the events using `async for`.

```python
import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

def lookup_order(order_id: str) -> dict:
    """Looks up an order by its ID."""
    return {"order_id": order_id, "status": "shipped", "eta": "2 days"}

agent = LlmAgent(
    name="OrderBot",
    model="gemini-2.0-flash",
    instruction="Help customers check order status using the lookup_order tool.",
    tools=[lookup_order],
)

session_service = InMemorySessionService()
runner = Runner(agent=agent, session_service=session_service)

async def chat(user_input: str, user_id: str, session_id: str):
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(user_input)]
    )

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        # Skip partial streaming events if you only want final results
        if event.partial:
            continue

        # Print agent responses
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[{event.author}]: {part.text}")
                elif part.function_call:
                    print(f"[Tool Call]: {part.function_call.name}({part.function_call.args})")
                elif part.function_response:
                    print(f"[Tool Result]: {part.function_response.response}")

        # Check for state changes
        if event.actions and event.actions.state_delta:
            print(f"[State Update]: {event.actions.state_delta}")

asyncio.run(chat("Where is order #12345?", "user1", "session1"))
```

For simpler cases, use `InMemoryRunner` which bundles session/artifact services:

```python
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(agent=agent)
# Same run_async interface, but session management is automatic
```

---

### Q16: How does the Runner orchestrate Agent + Session + Tools during a single invocation?
**Answer:** During a single invocation (one `run_async` call), the Runner executes a tight orchestration loop:

1. **Load Session**: `session_service.get_session(app_name, user_id, session_id)` retrieves the Session object with full event history and current state.
2. **Build InvocationContext**: The Runner creates an `InvocationContext` containing the session, agent reference, services, and a unique `invocation_id`.
3. **Agent Reasoning (LLM Call)**: The agent sends its instruction + conversation history + tool schemas to the LLM. The LLM returns either a text response or a function call.
4. **Tool Execution (if function call)**: If the LLM generates a `function_call`, the Runner resolves the tool by name, injects `ToolContext` if needed, executes the function, and creates a `function_response` Event. The function response is fed back to the LLM for another reasoning step (this loops until the LLM produces a text response or transfers to another agent).
5. **Agent Transfer (if transfer_to_agent)**: If the Event's actions contain `transfer_to_agent`, the Runner switches execution to the target agent, carrying forward the same session and invocation context.
6. **Event Persistence**: Each non-partial Event is appended to the session via `session_service.append_event(session, event)`, which updates both event history and state (via `state_delta`).
7. **Yield to Caller**: Each Event is yielded to the caller as it is produced, enabling streaming.

The tool execution loop (steps 3-4) is called the "agentic loop" -- the LLM keeps calling tools and reasoning until it has enough information to produce a final response. This is what makes agents autonomous rather than single-shot.

---

## Session & State (Q17-Q20)

### Q17: What are the different `SessionService` implementations and when do you use each?
**Answer:** ADK provides three `SessionService` implementations that determine how session data (conversation history, state) is stored:

| Implementation | Storage | Persistence | Use Case |
|---------------|---------|-------------|----------|
| **`InMemorySessionService`** | Application memory (RAM) | Lost on restart | Development, testing, prototyping, demos |
| **`DatabaseSessionService`** | Relational DB (PostgreSQL, MySQL, SQLite) | Persisted to disk | Self-managed production deployments |
| **`VertexAiSessionService`** | Google Cloud Vertex AI managed storage | Persisted, scalable | Google Cloud production deployments |

```python
# 1. In-Memory (development)
from google.adk.sessions import InMemorySessionService
session_service = InMemorySessionService()

# 2. Database (self-managed production)
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(
    db_url="postgresql+asyncpg://user:pass@localhost:5432/adk_db"
    # Also supports: "sqlite+aiosqlite:///local.db"
    # Also supports: "mysql+aiomysql://user:pass@host/db"
)

# 3. Vertex AI (Google Cloud managed)
from google.adk.sessions import VertexAiSessionService
session_service = VertexAiSessionService(
    project="my-gcp-project",
    location="us-central1",
)

# All share the same interface
session = await session_service.create_session(
    app_name="my_app",
    user_id="user123",
    state={"user:name": "Alice"},
)
```

`DatabaseSessionService` requires async database drivers (`asyncpg`, `aiosqlite`, `aiomysql`). `VertexAiSessionService` requires a GCP project with Vertex AI APIs enabled and optionally a Reasoning Engine resource.

---

### Q18: Explain state key prefixes (`app:`, `user:`, `temp:`, no prefix) and their persistence rules.
**Answer:** State key prefixes in ADK define the scope and persistence behavior of state entries. The `SessionService` uses these prefixes to route state to the correct storage scope:

| Prefix | Scope | Shared Across | Persistence (DB/Vertex) | Persistence (InMemory) |
|--------|-------|---------------|------------------------|----------------------|
| **(none)** | Session-specific | Only this session | Persisted | Lost on restart |
| **`user:`** | User-specific | All sessions for this `user_id` within same `app_name` | Persisted | Lost on restart |
| **`app:`** | Application-wide | All users, all sessions for this `app_name` | Persisted | Lost on restart |
| **`temp:`** | Invocation-only | Only current `run_async` call | **Never persisted** | **Never persisted** |

```python
def process_request(query: str, tool_context: ToolContext) -> dict:
    """Example showing all prefix scopes."""

    # Session state -- specific to this conversation thread
    tool_context.state["current_step"] = "processing"

    # User state -- follows the user across sessions
    tool_context.state["user:preferred_language"] = "en"
    tool_context.state["user:login_count"] = tool_context.state.get("user:login_count", 0) + 1

    # App state -- shared across ALL users and sessions
    tool_context.state["app:total_requests"] = tool_context.state.get("app:total_requests", 0) + 1
    tool_context.state["app:global_discount"] = "SAVE10"

    # Temp state -- discarded after this invocation completes
    tool_context.state["temp:raw_api_response"] = {"large": "payload"}
    tool_context.state["temp:intermediate_calc"] = 42

    return {"status": "done"}
```

Key insight: `temp:` state is useful for passing large intermediate data between tools within a single invocation without polluting persistent storage. The `SessionService` handles merging user/app state from the correct underlying storage based on prefixes.

---

### Q19: How is state updated via `append_event` and why should you never modify state directly?
**Answer:** State in ADK is event-sourced -- all state changes are captured as `state_delta` within Events and applied by the `SessionService` when `append_event()` is called. This ensures that state changes are tracked in history, persisted correctly, and thread-safe.

**The correct ways to update state:**

```python
# Method 1: Via ToolContext (most common -- inside tool functions)
def my_tool(query: str, tool_context: ToolContext) -> dict:
    tool_context.state["result"] = "computed_value"  # Tracked as state_delta
    return {"status": "ok"}

# Method 2: Via CallbackContext (inside agent callbacks)
def on_before_agent(callback_context):
    callback_context.state["visit_count"] = callback_context.state.get("visit_count", 0) + 1

# Method 3: Via output_key (automatic -- agent response saved to state)
agent = LlmAgent(name="A", model="gemini-2.0-flash", output_key="answer")

# Method 4: Manually via append_event (for system-level updates)
import time
from google.adk.events import Event, EventActions

event = Event(
    invocation_id="inv_001",
    author="system",
    actions=EventActions(state_delta={
        "task_status": "active",
        "user:login_count": 5,
    }),
    timestamp=time.time(),
)
await session_service.append_event(session, event)
```

**Why NEVER modify state directly:**

```python
# WRONG -- bypasses event tracking, breaks persistence and thread safety
session = await session_service.get_session(...)
session.state["key"] = "value"  # This change is NOT tracked or persisted!

# RIGHT -- changes flow through events
tool_context.state["key"] = "value"  # Creates state_delta in the event
```

Direct modification breaks: (1) event history (no record of when/why state changed), (2) persistence (changes not written to DB/Vertex), (3) thread safety (no locking), (4) timestamp tracking.

---

### Q20: How do you access state values inside agent instructions using template syntax?
**Answer:** ADK supports `{key}` template syntax in agent instructions to inject state values at runtime. When the Runner prepares the instruction for the LLM, it resolves `{key}` references against `session.state`. This works with all state prefixes.

```python
# Simple templating -- state keys referenced with {key}
agent = LlmAgent(
    name="Greeter",
    model="gemini-2.0-flash",
    instruction="Greet the user by name: {user:name}. Their preferred language is {user:lang}.",
)

# The instruction resolves to: "Greet the user by name: Alice. Their preferred language is en."
# (assuming state has user:name = "Alice" and user:lang = "en")
```

**Problem**: If your instruction contains literal curly braces (e.g., JSON examples), the template engine will try to resolve them. Use an `InstructionProvider` callable instead:

```python
from google.adk.agents import ReadonlyContext
from google.adk.utils import instructions_utils

# Option 1: Callable instruction provider (bypasses templating)
def my_instruction(context: ReadonlyContext) -> str:
    name = context.state.get("user:name", "User")
    return f'Hello {name}. Format output as JSON: {{"key": "value"}}'

agent = LlmAgent(
    name="JsonHelper",
    model="gemini-2.0-flash",
    instruction=my_instruction,  # Callable, not a string
)

# Option 2: Selective injection with inject_session_state
async def dynamic_instruction(context: ReadonlyContext) -> str:
    template = "Help {user:name}. Use JSON format: {\"result\": \"<answer>\"}"
    return await instructions_utils.inject_session_state(template, context)
```

The callable approach gives you full control: you can read state, fetch external config, or conditionally construct instructions based on runtime context.

---

## Multi-Agent Orchestration (Q21-Q24)

### Q21: How does LLM-driven delegation work with `transfer_to_agent`?
**Answer:** LLM-driven delegation is ADK's mechanism for dynamic agent routing. When a parent `LlmAgent` has `sub_agents`, the framework exposes a `transfer_to_agent(agent_name)` function to the LLM. The LLM can generate a function call to this function to transfer control to a child agent. The framework's `AutoFlow` intercepts this call and switches execution to the target agent.

```python
booking_agent = LlmAgent(
    name="BookingAgent",
    model="gemini-2.0-flash",
    description="Handles flight and hotel bookings.",  # LLM reads this to decide
    instruction="Help users book flights and hotels.",
    tools=[search_flights, book_hotel],
)

support_agent = LlmAgent(
    name="SupportAgent",
    model="gemini-2.0-flash",
    description="Handles complaints, refunds, and support issues.",
    instruction="Help users with complaints and refunds.",
    tools=[create_ticket, process_refund],
)

coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="""You are a travel assistant coordinator.
    - For booking requests, transfer to BookingAgent.
    - For complaints or refunds, transfer to SupportAgent.
    - For general questions, answer directly.""",
    sub_agents=[booking_agent, support_agent],
)
```

When a user says "I want to book a flight to Paris", the coordinator LLM generates:
```
function_call: transfer_to_agent(agent_name="BookingAgent")
```

The framework then routes execution to `BookingAgent`, which takes over the conversation. The `description` field on sub-agents is critical -- it tells the parent LLM what each child does, enabling intelligent routing decisions.

---

### Q22: How does hierarchical agent composition work with `sub_agents`?
**Answer:** ADK agents form tree structures through the `sub_agents` parameter. Each agent can have children, and children can have their own children, forming a hierarchy. An agent instance can only be added as a sub-agent once -- attempting to assign a second parent raises a `ValueError`. The framework automatically sets `parent_agent` on children.

```python
# Level 3: Leaf specialist agents
flight_search = LlmAgent(name="FlightSearch", model="gemini-2.0-flash",
    instruction="Search for flights.", tools=[search_flights_api])
hotel_search = LlmAgent(name="HotelSearch", model="gemini-2.0-flash",
    instruction="Search for hotels.", tools=[search_hotels_api])
payment_processor = LlmAgent(name="PaymentProcessor", model="gemini-2.0-flash",
    instruction="Process payments.", tools=[charge_card])

# Level 2: Mid-level coordinators
travel_planner = LlmAgent(
    name="TravelPlanner",
    model="gemini-2.0-flash",
    description="Plans complete travel itineraries.",
    instruction="Coordinate flight and hotel searches for the user.",
    sub_agents=[flight_search, hotel_search],  # Can delegate down
)

# Level 1: Top-level orchestrator
root = LlmAgent(
    name="TravelBot",
    model="gemini-2.0-flash",
    instruction="""You are the main travel assistant.
    For trip planning, delegate to TravelPlanner.
    For payments, delegate to PaymentProcessor.""",
    sub_agents=[travel_planner, payment_processor],
)

# The tree: TravelBot -> [TravelPlanner -> [FlightSearch, HotelSearch], PaymentProcessor]
```

Three interaction mechanisms exist within the hierarchy:
1. **Shared Session State**: Agents read/write `session.state` (passive communication via `output_key`)
2. **LLM-Driven Transfer**: Parent generates `transfer_to_agent()` to delegate
3. **AgentTool**: Wrap a child as a tool for explicit invocation with result return

---

### Q23: What is the A2A (Agent-to-Agent) protocol and how does it relate to ADK?
**Answer:** A2A (Agent-to-Agent) is an open protocol by Google for standardized communication between AI agents running as separate services, potentially on different machines and built with different frameworks. It uses HTTP, Server-Sent Events (SSE), and JSON-RPC. A2A and ADK are complementary:

- **ADK** answers: "How do I build and orchestrate agents within my system?"
- **A2A** answers: "How do agents from different systems/organizations talk to each other?"

Key A2A concepts:
- **Agent Card**: A JSON document at a well-known endpoint (e.g., `/.well-known/agent.json`) describing an agent's capabilities, supported input/output types, and authentication requirements. Enables agent discovery.
- **Tasks**: The unit of work in A2A. A client sends a task to a remote agent, which processes it and returns results.
- **Streaming**: Real-time updates via SSE for long-running tasks.

```python
# Converting an ADK agent to A2A-compatible service
from google.adk.agents import LlmAgent

# Build your agent with ADK
my_agent = LlmAgent(
    name="DocumentAnalyzer",
    model="gemini-2.0-flash",
    instruction="Analyze documents and extract key information.",
    tools=[extract_text, summarize],
)

# Expose as A2A service (using ADK's A2A integration)
# The agent becomes discoverable via its Agent Card
# Other agents (even non-ADK agents) can send tasks to it via HTTP
```

Use A2A when you need cross-organization agent interoperability, microservice-style agent architectures, or integration with agents built in other frameworks (LangChain, CrewAI, etc.).

---

### Q24: Describe common multi-agent orchestration patterns in ADK.
**Answer:** ADK supports several well-established multi-agent patterns:

**1. Coordinator/Dispatcher Pattern** -- Central LLM agent routes requests to specialists:
```python
coordinator = LlmAgent(
    name="Dispatcher", model="gemini-2.0-flash",
    instruction="Route to the right specialist.",
    sub_agents=[billing_agent, tech_agent, sales_agent],
)
```

**2. Sequential Pipeline** -- Fixed-order processing with state passing:
```python
pipeline = SequentialAgent(name="ETL", sub_agents=[
    extractor,    # output_key="raw_data"
    transformer,  # reads {raw_data}, output_key="clean_data"
    loader,       # reads {clean_data}
])
```

**3. Parallel Fan-Out / Gather** -- Independent tasks run concurrently, then aggregated:
```python
fan_out = ParallelAgent(name="Gather", sub_agents=[
    weather_agent,  # output_key="weather"
    news_agent,     # output_key="news"
    stock_agent,    # output_key="stocks"
])
pipeline = SequentialAgent(name="Report", sub_agents=[fan_out, summarizer])
```

**4. Iterative Refinement (Critique-Revise Loop)**:
```python
loop = LoopAgent(name="Refine", max_iterations=5, sub_agents=[
    writer,   # output_key="draft"
    critic,   # reads {draft}, output_key="feedback"
    checker,  # reads {feedback}, escalates if quality >= threshold
])
```

**5. Hierarchical Task Decomposition** -- Multi-level delegation:
```python
root = LlmAgent(name="PM", sub_agents=[
    LlmAgent(name="Frontend", sub_agents=[react_agent, css_agent]),
    LlmAgent(name="Backend", sub_agents=[api_agent, db_agent]),
])
```

**6. Human-in-the-Loop** -- Agent pauses for human approval using callbacks or tool confirmation policies before executing sensitive actions.

The key design principle: combine workflow agents for structure with LLM agents for flexibility. Use `output_key` + state templates for data flow, and `transfer_to_agent` for dynamic routing.

---

## RAG with ADK (Q25-Q26)

### Q25: How do you use the `VertexAiRagRetrieval` built-in tool for RAG in ADK?
**Answer:** `VertexAiRagRetrieval` is ADK's built-in tool for Retrieval-Augmented Generation using Vertex AI RAG Engine. It enables agents to search against indexed documents (from GCS, Google Drive, or local files) stored in a Vertex AI RAG Corpus. The RAG Engine handles chunking, embedding, indexing, and retrieval automatically.

```python
from google.adk.agents import LlmAgent
from google.adk.tools.retrieval import VertexAiRagRetrieval

# Create the RAG retrieval tool pointing to your corpus
rag_tool = VertexAiRagRetrieval(
    name="search_company_docs",
    description="Search internal company documents, policies, and knowledge base.",
    rag_corpus_name="projects/my-project/locations/us-central1/ragCorpora/123456",
    similarity_top_k=5,             # Number of chunks to retrieve
    vector_distance_threshold=0.7,   # Minimum similarity score
)

# Create an agent with RAG grounding
support_agent = LlmAgent(
    name="PolicyExpert",
    model="gemini-2.0-flash",
    instruction="""You are a company policy expert.
    When asked about policies or procedures, use the search_company_docs tool
    to find relevant information. Always cite the source document.
    If no relevant documents are found, say so clearly.""",
    tools=[rag_tool],
)
```

The RAG process flow: (1) User asks a question. (2) The LLM decides to call `search_company_docs`. (3) The tool queries the Vertex AI RAG Engine corpus. (4) Relevant document chunks are returned with metadata. (5) The LLM uses the retrieved context to generate a grounded answer.

Prerequisites: Create a RAG Corpus in Vertex AI, ingest documents (GCS, Drive, or local), and note the corpus resource name. The corpus handles chunking and embedding automatically.

---

### Q26: How would you build a custom agentic RAG pipeline (retriever + relevancy + rewriter) in ADK?
**Answer:** For more control than the built-in `VertexAiRagRetrieval`, you can build a custom agentic RAG loop using ADK's multi-agent patterns. This allows you to add relevancy checking, query rewriting, and iterative refinement:

```python
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent

# Tool: Custom retriever (e.g., calling your own vector DB)
def search_vector_db(query: str, top_k: int = 5) -> dict:
    """Searches the vector database for documents relevant to the query."""
    # Your Pinecone/Weaviate/ChromaDB/pgvector call here
    results = my_vector_db.search(query, top_k=top_k)
    return {"chunks": results, "query": query}

# Step 1: Retriever agent -- searches and saves results to state
retriever = LlmAgent(
    name="Retriever",
    model="gemini-2.0-flash",
    instruction="Search for documents relevant to: {user_query}. Use the search tool.",
    tools=[search_vector_db],
    output_key="retrieved_chunks",
)

# Step 2: Relevancy checker -- evaluates if chunks answer the question
relevancy_checker = LlmAgent(
    name="RelevancyChecker",
    model="gemini-2.0-flash",
    instruction="""Evaluate if the retrieved chunks adequately answer the query.
    Query: {user_query}
    Chunks: {retrieved_chunks}

    If relevant, set relevancy_status to 'sufficient' and escalate.
    If not relevant, set relevancy_status to 'insufficient' and suggest a rewritten query.""",
    output_key="relevancy_result",
)

# Step 3: Query rewriter -- reformulates query if chunks were irrelevant
query_rewriter = LlmAgent(
    name="QueryRewriter",
    model="gemini-2.0-flash",
    instruction="""The previous query did not retrieve relevant results.
    Original query: {user_query}
    Feedback: {relevancy_result}
    Rewrite the query to be more specific or use different terms.""",
    output_key="user_query",  # Overwrites the original query for next loop iteration
)

# Agentic RAG loop: retrieve -> check relevancy -> rewrite if needed
rag_loop = LoopAgent(
    name="RAGLoop",
    max_iterations=3,
    sub_agents=[retriever, relevancy_checker, query_rewriter],
)

# Final answer generator
answer_generator = LlmAgent(
    name="AnswerGenerator",
    model="gemini-2.0-flash",
    instruction="""Generate a comprehensive answer based on:
    Query: {user_query}
    Retrieved context: {retrieved_chunks}
    Cite sources. If context is insufficient, acknowledge limitations.""",
    output_key="final_answer",
)

# Full pipeline
rag_pipeline = SequentialAgent(
    name="AgenticRAG",
    sub_agents=[rag_loop, answer_generator],
)
```

You can also use MCP-based RAG by connecting to an MCP server that wraps your vector database, giving you the same retrieval capability through the standardized MCP protocol.

---

## Model Support (Q27-Q28)

### Q27: How does ADK support Gemini models natively and what is the model parameter format?
**Answer:** ADK is optimized for Google Gemini models, which can be specified as simple string identifiers in the `model` parameter. Gemini models are accessed either through Google AI Studio (API key) or Vertex AI (GCP project).

```python
from google.adk.agents import LlmAgent

# Gemini model strings (Google AI Studio)
agent_flash = LlmAgent(name="A", model="gemini-2.0-flash", instruction="...")
agent_pro = LlmAgent(name="B", model="gemini-1.5-pro", instruction="...")
agent_latest = LlmAgent(name="C", model="gemini-flash-latest", instruction="...")

# Environment setup for Google AI Studio
# export GOOGLE_API_KEY="your-api-key"

# For Vertex AI, set project and location
# export GOOGLE_CLOUD_PROJECT="my-project"
# export GOOGLE_CLOUD_LOCATION="us-central1"
```

Gemini models support all ADK features natively: function calling (tools), multi-turn conversations, streaming, code execution, grounding with Google Search, and multimodal inputs (text, images, audio, video). The `generate_content_config` parameter allows fine-tuning LLM behavior:

```python
from google.genai import types

agent = LlmAgent(
    name="CreativeWriter",
    model="gemini-2.0-flash",
    instruction="Write creative stories.",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.9,
        top_p=0.95,
        max_output_tokens=2048,
    ),
)
```

ADK also supports Claude models on Vertex AI as string identifiers (e.g., `"claude-3-5-sonnet@20241022"`) when accessed through Vertex AI Model Garden.

---

### Q28: How do you use non-Gemini models (OpenAI, Claude, Mistral, local models) with ADK via LiteLLM?
**Answer:** ADK uses model connector objects for non-Gemini models. The primary adapter is `LiteLlm`, which provides access to 100+ LLM providers through the LiteLLM library. For local models, ADK supports Ollama and vLLM connectors.

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# OpenAI GPT-4o
# export OPENAI_API_KEY="sk-..."
openai_agent = LlmAgent(
    name="GPT4Agent",
    model=LiteLlm(model="openai/gpt-4o"),
    instruction="You are a helpful assistant.",
    tools=[my_tool],
)

# Anthropic Claude
# export ANTHROPIC_API_KEY="sk-ant-..."
claude_agent = LlmAgent(
    name="ClaudeAgent",
    model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    instruction="You are a helpful assistant.",
)

# Mistral
# export MISTRAL_API_KEY="..."
mistral_agent = LlmAgent(
    name="MistralAgent",
    model=LiteLlm(model="mistral/mistral-large-latest"),
    instruction="You are a helpful assistant.",
)

# Local model via Ollama
from google.adk.models.ollama_llm import OllamaLlm

local_agent = LlmAgent(
    name="LocalAgent",
    model=OllamaLlm(model="llama3.2"),  # Requires Ollama running locally
    instruction="You are a helpful assistant.",
)

# Local model via vLLM
from google.adk.models.vllm_llm import VllmLlm

vllm_agent = LlmAgent(
    name="VllmAgent",
    model=VllmLlm(model="meta-llama/Llama-3-8b", base_url="http://localhost:8000"),
    instruction="You are a helpful assistant.",
)
```

This model-agnostic design means you can mix models within a multi-agent system -- use Gemini for the coordinator (best function calling), Claude for complex reasoning tasks, and a local model for sensitive data processing. Install LiteLLM support with `pip install google-adk[litellm]`.

**Important caveat**: Not all models support all features equally. Tool/function calling support varies by provider, and some ADK features (like built-in Google Search grounding) are Gemini-only.

---

## Deployment & Dev Tools (Q29-Q30)

### Q29: What CLI tools does ADK provide for development (`adk create`, `adk web`, `adk run`)?
**Answer:** ADK ships with a CLI (`adk`) that provides three key development commands:

**`adk create`** -- Scaffolds a new agent project with the correct directory structure:
```bash
adk create my_agent
# Creates:
# my_agent/
#   __init__.py
#   agent.py         # Agent definition (must define root_agent)
#   .env             # Environment variables (API keys)
```
The generated `agent.py` contains a starter `root_agent` definition that ADK tools expect.

**`adk run`** -- Runs your agent in the terminal for interactive testing:
```bash
adk run my_agent
# Starts a REPL where you type messages and see agent responses
# Uses InMemorySessionService by default
```

**`adk web`** -- Launches a browser-based development UI:
```bash
adk web my_agent
# Opens http://localhost:8000 with:
# - Chat interface for testing conversations
# - Event inspector showing all events, tool calls, state changes
# - Session management (create/switch sessions)
# - State viewer for real-time state inspection
# - Trace viewer for debugging agent reasoning
```

The `adk web` UI is invaluable during development -- it shows the full event stream including intermediate tool calls, state deltas, and agent transfers, making it easy to debug multi-agent orchestration. The UI uses `InMemorySessionService` by default, so data is lost on restart.

Additional CLI commands:
- **`adk eval`** -- Run evaluation sets from the command line
- **`adk deploy cloud_run`** -- Deploy to Google Cloud Run
- **`adk deploy agent_engine`** -- Deploy to Vertex AI Agent Engine
- **`adk api_server`** -- Start a production API server

---

### Q30: How do you deploy ADK agents to production (Cloud Run, Vertex AI Agent Engine, GKE) and how does the evaluation framework work?
**Answer:** ADK supports three primary deployment targets and includes a built-in evaluation framework:

**Cloud Run Deployment:**
```bash
adk deploy cloud_run \
    --project=my-gcp-project \
    --region=us-central1 \
    --service_name=my-agent-service \
    --with_ui  # Optional: deploy dev UI alongside API
    my_agent/
```
This automatically builds a container, pushes to Artifact Registry, and deploys to Cloud Run. The `--with_ui` flag is useful for staging environments.

**Vertex AI Agent Engine:**
```bash
adk deploy agent_engine \
    --project=my-gcp-project \
    --region=us-central1 \
    my_agent/
```
Agent Engine is Google's fully managed runtime for agents -- it handles scaling, session management (built-in `VertexAiSessionService`), monitoring, and versioning. This is the recommended production deployment for Google Cloud users.

**GKE (Google Kubernetes Engine):** Deploy as a standard containerized application with Kubernetes manifests. ADK agents are regular Python applications, so any container orchestration platform works.

**Evaluation Framework:**

ADK provides three evaluation methods:

1. **`adk eval` CLI** -- Run evaluations from test files:
```bash
adk eval my_agent/ --eval_set my_tests.test.json
```

2. **pytest integration** -- Programmatic evaluation in CI/CD:
```python
import pytest
from google.adk.evaluation import AgentEvaluator

@pytest.mark.asyncio
async def test_agent_quality():
    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        agent_name="root_agent",
        eval_dataset_file_path="tests/eval_data.test.json",
    )
```

3. **Test file format** (`.test.json`):
```json
[{
    "query": "What is the weather in London?",
    "expected_tool_use": [{"tool_name": "get_weather", "tool_input": {"city": "London"}}],
    "expected_intermediate_agent_responses": [],
    "reference": "The weather in London is cloudy with 18 degrees."
}]
```

Evaluation metrics include:
- **`tool_trajectory_avg_score`**: Compares actual vs. expected tool call sequences (EXACT, IN_ORDER, ANY_ORDER matching)
- **`response_match_score`**: Semantic similarity to reference answers
- **`final_response_match_v2`**: LLM-as-judge for response quality
- **`hallucinations_v1`**: Checks each sentence for grounding
- **`safety_v1`**: Harmlessness scoring via Vertex AI Eval SDK

---

## Quick Reference: Key ADK Imports

```python
# Agents
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent, BaseAgent

# Runner
from google.adk.runners import Runner, InMemoryRunner

# Sessions
from google.adk.sessions import InMemorySessionService, DatabaseSessionService, VertexAiSessionService

# Tools
from google.adk.tools import FunctionTool, google_search, built_in_code_execution, ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.retrieval import VertexAiRagRetrieval

# Models
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.ollama_llm import OllamaLlm

# Events
from google.adk.events import Event, EventActions

# Evaluation
from google.adk.evaluation import AgentEvaluator

# Types
from google.genai import types
```
