# LangGraph Interview Questions & Answers

---

## Core Concepts

---

**Q1. What is LangGraph and how does it differ from LangChain?**

LangChain is a library for building LLM-powered pipelines using chains — linear sequences of steps. LangGraph extends this by introducing a **graph-based execution model** built on top of LangChain primitives. The key difference is **cycles** — LangChain chains are DAGs (directed acyclic graphs), meaning data flows in one direction. LangGraph allows edges that loop back, enabling iterative agent behaviours like retry loops, reflection, and multi-turn tool use. LangGraph also introduces first-class **state management**, **checkpointing**, and **human-in-the-loop** patterns that LangChain chains do not support natively.

---

**Q2. What is a StateGraph and how does it work?**

A `StateGraph` is the core abstraction in LangGraph. You define it with a state schema (a TypedDict or Pydantic model), then add nodes (Python functions) and edges (transitions between nodes). Each node receives the current state and returns a partial dict of updates. LangGraph merges these updates into the state before passing it to the next node. The graph is compiled into a `CompiledGraph` which is a runnable — you invoke it with an initial state and it executes the nodes following the defined edges until it reaches `END`.

---

**Q3. How does state work in LangGraph? What happens when a node returns a partial state update?**

State is a typed dictionary shared across all nodes. When a node returns `{"key": value}`, LangGraph merges that into the existing state using a **reducer function**. The default reducer is simple replacement — the new value overwrites the old one. For list fields like `messages`, you can specify an `add_messages` reducer using `Annotated[list[BaseMessage], add_messages]` which appends new messages instead of replacing. This merge-based approach means nodes only need to return what they changed, not the full state.

---

**Q4. What are reducers in LangGraph state and why are they important?**

Reducers define how state updates are merged when a node returns a partial update. Without a custom reducer, returning `{"messages": [new_msg]}` would replace the entire messages list. With the `add_messages` reducer, it appends instead. You can write custom reducers for any merge logic — deduplication, max-length truncation, merging dicts, etc. Reducers are critical for accumulation patterns (chat history, tool results) where each node adds to the state rather than replacing it.

---

**Q5. What is the difference between `add_edge` and `add_conditional_edges`?**

`add_edge("A", "B")` creates a fixed transition — after node A completes, node B always runs next. `add_conditional_edges("A", router_fn, mapping)` creates a dynamic transition — after node A completes, `router_fn` is called with the current state and returns a string key. The `mapping` dict maps that key to the next node name. This is how you implement branching logic — for example routing to different nodes based on intent, or deciding whether to retry or end.

---

**Q6. What does `graph.compile()` do and what is a CompiledGraph?**

`graph.compile()` validates the graph structure (checks for unreachable nodes, missing edges, etc.) and returns a `CompiledGraph`. The compiled graph is a LangChain `Runnable` — it supports `.invoke()`, `.ainvoke()`, `.stream()`, and `.astream()`. Compilation also wires up checkpointing if a checkpointer is provided. You define the graph once and compile it once; the compiled graph is reused across all invocations.

---

**Q7. How do you create cycles (loops) in LangGraph? Why is this significant?**

You create cycles by adding a conditional edge that routes back to a previous node. For example: `respond → evaluate → (if ungrounded) → respond`. The conditional edge function inspects the state and returns either `"retry"` (back to respond) or `"done"` (to END). This is significant because it enables **iterative agent patterns** — self-correction, reflection, multi-step tool use, and retry loops — which are impossible in a linear chain. You should always include a counter or max-retry field in state to prevent infinite loops.

---

**Q8. What is the `END` sentinel in LangGraph?**

`END` is a special constant imported from `langgraph.graph` that represents the terminal node. When an edge points to `END`, the graph execution stops and the final state is returned to the caller. You can have multiple edges pointing to `END` from different nodes — for example, both a "blocked" path and a "success" path can terminate the graph. Every valid graph must have at least one path that reaches `END`.

---

## Checkpointing & Persistence

---

**Q9. What is checkpointing in LangGraph and why would you use it?**

Checkpointing persists the graph state after each node execution. If the process crashes mid-graph, you can resume from the last checkpoint instead of restarting from scratch. It also enables **time travel** — inspecting or replaying the state at any point in the execution. You enable it by passing a checkpointer (e.g. `MemorySaver`, `SqliteSaver`, `PostgresSaver`) to `graph.compile(checkpointer=...)`. Each run is identified by a `thread_id` in the config, so multiple concurrent conversations can be checkpointed independently.

---

**Q10. What is the difference between MemorySaver and a persistent checkpointer like PostgresSaver?**

`MemorySaver` stores checkpoints in-memory — fast but lost on process restart. Useful for development and testing. `PostgresSaver` (or `SqliteSaver`, `MongoDBSaver`) persists checkpoints to a database — survives restarts, supports multi-process deployments, and enables long-running conversations. In production, you need a persistent checkpointer if you want conversation continuity across deployments or if your agent runs as a stateless container.

---

**Q11. How does `thread_id` work in LangGraph's checkpointing?**

`thread_id` is passed in the config dict: `{"configurable": {"thread_id": "abc123"}}`. It acts as a session identifier — all checkpoints for the same thread_id belong to the same conversation. When you invoke the graph with an existing thread_id, LangGraph loads the latest checkpoint and resumes from that state. Different thread_ids are completely isolated. This is how you maintain separate conversation histories for different users or sessions.

---

**Q12. Can you replay or inspect intermediate states of a graph execution?**

Yes. With checkpointing enabled, every node execution creates a checkpoint. You can use `graph.get_state_history(config)` to retrieve all checkpoints for a thread, giving you the full state at every step. You can also use `graph.update_state(config, values)` to modify a past state and re-run from that point. This is powerful for debugging — you can see exactly what the state looked like before and after each node.

---

## Human-in-the-Loop

---

**Q13. How does LangGraph support human-in-the-loop patterns?**

LangGraph provides an `interrupt()` function and `interrupt_before` / `interrupt_after` parameters on nodes. When a node is configured with `interrupt_before=True`, the graph pauses execution before that node, persists the state via checkpointing, and returns control to the caller. The caller (a UI, API, or human operator) can inspect the state, modify it if needed, and then resume execution by re-invoking the graph with the same thread_id. This enables approval workflows, manual corrections, and interactive debugging.

---

**Q14. What is the difference between `interrupt_before` and `interrupt_after`?**

`interrupt_before` pauses the graph before the node runs — useful when you want a human to approve or modify the input before the node processes it (e.g. approve a tool call before execution). `interrupt_after` pauses after the node runs — useful when you want a human to review the node's output before the graph continues (e.g. review a draft response before sending it). Both require checkpointing to persist the paused state.

---

**Q15. How would you implement an approval step where a human reviews the agent's proposed tool calls before execution?**

Add `interrupt_before=["execute_tools"]` when compiling the graph. When the graph reaches the tool execution node, it pauses and returns the current state (which includes the proposed tool calls). The caller inspects the tool calls, optionally modifies or removes them using `graph.update_state()`, and then resumes the graph with `graph.invoke(None, config)`. The tool executor runs with whatever tool calls are in the (potentially modified) state. This gives full human control over what the agent actually executes.

---

## Streaming

---

**Q16. What streaming modes does LangGraph support?**

LangGraph supports multiple streaming modes: `"values"` streams the full state after each node, `"updates"` streams only the state delta (what each node changed), `"messages"` streams LLM tokens as they are generated (for real-time typing indicators), and `"events"` streams detailed execution events. You can combine modes: `graph.astream(input, config, stream_mode=["updates", "messages"])`. The `"messages"` mode is particularly useful for chat UIs where you want to show the response as it is being generated.

---

**Q17. How does token-level streaming work in LangGraph?**

When using `stream_mode="messages"`, LangGraph intercepts the LLM's streaming output and yields individual token chunks as they arrive. Each chunk includes metadata about which node generated it. This works because LangGraph nodes that call LLMs use LangChain's streaming-capable models. The graph does not wait for the full LLM response before streaming — tokens flow through in real time. This is essential for chat applications where users expect to see the response forming progressively.

---

## Subgraphs & Multi-Agent

---

**Q18. What are subgraphs in LangGraph and when would you use them?**

A subgraph is a compiled graph used as a node inside a parent graph. You add it with `parent_graph.add_node("sub", child_graph)`. Subgraphs are useful for: encapsulating complex logic (e.g. a multi-step RAG pipeline as a single node), reusing graph components across different parent graphs, and running different agent architectures for different tasks within one orchestrator. The subgraph has its own state schema — LangGraph handles mapping between parent and child state.

---

**Q19. How do you build a multi-agent system in LangGraph?**

There are two primary patterns. **Supervisor pattern**: a parent graph has a supervisor node that decides which agent (subgraph) to delegate to, routes to it, collects the result, and decides whether to delegate again or respond. **Swarm pattern**: each agent is a node that can hand off to any other agent via conditional edges — there is no central supervisor. The supervisor pattern gives more control and is easier to debug. The swarm pattern is more flexible for peer-to-peer collaboration. Both use subgraphs to encapsulate each agent's logic.

---

**Q20. How does state mapping work between a parent graph and a subgraph?**

If the subgraph state schema is a subset of the parent schema, LangGraph automatically maps matching field names. If the schemas differ, you wrap the subgraph node in a function that transforms the parent state into the subgraph's expected input and maps the subgraph's output back to parent state fields. This explicit mapping keeps subgraphs decoupled — they do not need to know the parent's full schema, only their own inputs and outputs.

---

## Advanced Patterns

---

**Q21. How would you implement a reflection/self-correction loop in LangGraph?**

Create a cycle: `generate → evaluate → (conditional) → generate or END`. The generate node produces output, the evaluate node scores or critiques it (using an LLM or heuristic), and the conditional edge either loops back to generate with feedback injected into state, or proceeds to END if quality is acceptable. Add a `retries` counter in state and cap it to prevent infinite loops. The feedback from the evaluator should be added to state so the generator can use it on the next attempt.

---

**Q22. What is the `Send` API in LangGraph and how does it enable map-reduce patterns?**

`Send` allows a conditional edge to dispatch to the **same node multiple times in parallel** with different inputs. For example, if you need to process 5 documents independently, the router returns `[Send("process_doc", {"doc": d}) for d in docs]`. LangGraph runs 5 parallel instances of the `process_doc` node, each with its own input. The results are collected using a reducer. This is the map phase. A subsequent node aggregates the results (reduce phase). This pattern is useful for parallel RAG, batch processing, and fan-out/fan-in workflows.

---

**Q23. How does error handling work in LangGraph nodes?**

If a node raises an exception, the graph execution stops and the exception propagates to the caller. With checkpointing enabled, the state before the failed node is persisted, so you can fix the issue and resume. For graceful handling within the graph, you catch exceptions inside the node and write error information to state — then a conditional edge can route to a fallback or retry node. LangGraph also supports `retry_policy` on nodes for automatic retries with backoff on transient failures.

---

**Q24. What is `retry_policy` in LangGraph and how do you configure it?**

You can pass a `RetryPolicy` when adding a node: `graph.add_node("my_node", my_fn, retry_policy=RetryPolicy(max_attempts=3))`. If the node raises an exception, LangGraph automatically retries it up to `max_attempts` times with exponential backoff. You can configure `initial_interval`, `backoff_factor`, and `retry_on` (a function that decides which exceptions are retryable). This is useful for nodes that call external APIs where transient failures are expected.

---

**Q25. How does LangGraph handle parallel node execution?**

When multiple nodes have no dependency between them (e.g. after a fan-out from `Send` or when multiple edges originate from the same node), LangGraph runs them concurrently using asyncio. Each parallel node receives the same input state snapshot — they cannot see each other's updates until all parallel nodes complete. After all parallel nodes finish, their outputs are merged into the state using reducers. This means parallel nodes must write to different state keys, or use list reducers that can merge concurrent appends.

---

## Deployment & Production

---

**Q26. What is LangGraph Platform (formerly LangGraph Cloud)?**

LangGraph Platform is a managed deployment service by LangSmith that hosts your compiled graph as an API. It handles scaling, checkpointing (with built-in persistent storage), streaming, and provides a REST API for invoking your graph. It also includes a studio UI for debugging and visualising graph executions. You define your graph in code, push it, and the platform serves it. It is an alternative to self-hosting your graph inside a FastAPI app.

---

**Q27. How would you deploy a LangGraph agent in a production FastAPI application?**

Compile the graph at module level (once, at import time) and expose it via a FastAPI endpoint. The endpoint receives the user's message, constructs the initial state, and calls `await graph.ainvoke(state, config)`. Use a persistent checkpointer (Postgres/MongoDB) for conversation continuity. Add a `/stream` endpoint that uses `graph.astream()` with Server-Sent Events for real-time token streaming. The compiled graph is thread-safe and stateless — all state lives in the checkpointer — so it scales horizontally behind a load balancer.

---

**Q28. How do you test a LangGraph graph?**

Test at three levels. **Unit test nodes** — each node is a plain Python function, so test it by passing a mock state dict and asserting the returned updates. **Test routing logic** — call the conditional edge functions with different states and assert the correct route string. **Integration test the full graph** — use `MemorySaver` as the checkpointer, invoke the graph with a test input, and assert the final state. For deterministic tests, mock the LLM calls using LangChain's `FakeListLLM` or by patching the model. Test cycles explicitly by verifying the graph terminates and does not loop infinitely.

---

**Q29. How does LangGraph integrate with LangSmith for observability?**

LangGraph is built on LangChain's `Runnable` interface, so it automatically emits traces to LangSmith when `LANGCHAIN_TRACING_V2=true` is set. Each graph invocation appears as a trace with nested spans for every node, LLM call, and tool execution. You can see the state at each step, token counts, latencies, and any errors. LangSmith also supports evaluations — you can run your graph against a test dataset and score the outputs using custom evaluators. This is essential for monitoring agent quality in production.

---

**Q30. What are the key differences between LangGraph and other agent frameworks like CrewAI or AutoGen?**

LangGraph is **low-level and explicit** — you define every node, edge, and state transition. This gives full control over execution flow, makes debugging straightforward, and avoids hidden magic. CrewAI is **high-level and role-based** — you define agents with roles and goals, and the framework handles orchestration. Good for rapid prototyping but harder to debug and customise. AutoGen focuses on **multi-agent conversation** — agents are defined as chat participants that talk to each other. LangGraph's advantage is predictability and composability — you can build any agent pattern (ReAct, plan-and-execute, reflection, multi-agent) using the same graph primitives, and you always know exactly what the execution path is.
