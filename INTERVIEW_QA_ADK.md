# RiteCare Field Service Document Intelligence -- Interview Q&A (ADK Architecture)

30 interview questions and detailed answers covering the Google ADK-based architecture with Gemini, FastAPI microservices, MongoDB Atlas Vector Search, Kafka, Slack, Traefik, and Airflow.

---

## Google ADK vs LangGraph

### Q1: Why did you migrate from LangGraph to Google ADK, and what were the key trade-offs?

**Answer:** The original LangGraph implementation used a three-node StateGraph pipeline -- `intent_classifier`, `tool_executor`, and `responder` -- each calling GPT-4o-mini. This meant every user query required at least three LLM round-trips: one to classify intent and decide which tools to call, one to execute tools, and one to synthesize a natural-language response. With Google ADK, the entire pipeline collapses into a single `Agent` definition. Gemini 2.5 Flash natively reads the function signatures and docstrings of the registered tools, decides which ones to call (including parallel calls), invokes them, and synthesizes the final response -- all in one logical turn. The main trade-offs are: (1) we lose the explicit, auditable graph structure that LangGraph provides -- there is no visible state machine to inspect or unit-test node by node; (2) we are now tightly coupled to Google's model ecosystem since ADK's tool-calling protocol is Gemini-native; (3) we gain significantly lower latency (one LLM orchestration pass instead of three), simpler code (45 lines for the entire agent definition vs. hundreds for graph + node functions + state schema), and built-in session management via `SessionService`.

### Q2: In the LangGraph version, the intent classifier had to output a structured intent like "BU2+BU4, TOOLS: BOTH". How does ADK handle intent classification?

**Answer:** ADK eliminates the explicit intent classification step entirely. The `Agent` receives the system instruction that describes all five business units and their purposes, plus the full list of tools with their docstrings. Gemini reads the user query and, using its function-calling capability, directly decides which tool(s) to invoke. For example, if a user asks "What is customer C-101's onboarding status and do you have any billing policies about late fees?", Gemini will issue two parallel tool calls: `get_onboarding_status(customer_id="C-101")` and `search_billing_statements(query="late fees policy")`. The model effectively performs intent classification implicitly as part of its function-calling reasoning. We no longer need an `AgentState` schema with `intent` and `tool_results` fields -- the Runner manages this internally through events.

### Q3: What is the `root_agent` variable name convention in ADK, and why does it matter?

**Answer:** Google ADK expects the entry-point agent to be named `root_agent` by convention. When the `Runner` is instantiated with `Runner(agent=root_agent, ...)`, it uses this agent as the top-level orchestrator. In our `agent/agent.py`, we define `root_agent = Agent(name="ritecare_agent", model="gemini-2.5-flash", instruction=SYSTEM_INSTRUCTION, tools=[...])`. If you are using ADK's CLI (`adk run`), it will look for `root_agent` in the module. The name passed to `Agent(name=...)` is the logical agent identifier used in session records and logs -- it does not have to match the Python variable name but the variable itself must be `root_agent` for the ADK CLI auto-discovery to work.

---

## ADK Agent, Runner, SessionService

### Q4: Walk through the lifecycle of a single query from the FastAPI `/query` endpoint through the ADK Runner.

**Answer:** The flow proceeds as follows: (1) The FastAPI endpoint receives a `QueryRequest` with `query`, `session_id`, `user_id`, and optional `bu_hint`. (2) We construct a `types.Content` object with `role="user"` and a single `Part(text=request.query)`. (3) We call `runner.run_async(user_id=request.user_id, session_id=request.session_id, new_message=content)`, which returns an async generator of events. (4) The Runner looks up or creates a session via `MongoSessionService` using the `session_id`. (5) It sends the conversation history plus the new message to Gemini 2.5 Flash with all registered tool schemas. (6) Gemini may respond with function-call requests -- the Runner executes those tool functions, collects results, and sends them back to the model. This tool-call loop continues until Gemini produces a final text response. (7) Each event in the generator has properties like `is_final_response()` and `content`. We iterate until we find the final response event and extract `event.content.parts[0].text`. (8) The event is appended to the session in MongoDB via `append_event`, so subsequent queries in the same session have full conversation context.

### Q5: Explain the `MongoSessionService` implementation. Why did you build a custom one instead of using ADK's built-in?

**Answer:** ADK ships with an `InMemorySessionService` that stores sessions in a Python dict -- this is unsuitable for production because sessions are lost on restart and cannot be shared across multiple agent instances. We subclass `BaseSessionService` and implement five methods: `create_session`, `get_session`, `list_sessions`, `delete_session`, and `append_event`. The backing store is a MongoDB collection called `adk_sessions`, accessed via Motor (async MongoDB driver). `create_session` inserts a full `Session` document. `get_session` looks up by session ID. The critical method is `append_event`, which uses `$push` to append the event to the `events` array and `$set` to update the session `state` -- this is an atomic operation so concurrent appends are safe. By storing sessions in MongoDB Atlas, we get persistence across restarts, horizontal scalability (any agent container can load any session), and natural backup/restore via Atlas.

### Q6: How does ADK handle conversation history differently from the previous LangGraph approach that used `trim_messages`?

**Answer:** In the LangGraph version, we manually maintained a list of messages in `AgentState` and used a `trim_messages` utility to keep the token count under `max_history_tokens` (3000 tokens). We had to count tokens ourselves, decide where to truncate, and manage the sliding window. With ADK's `SessionService`, the Runner manages conversation history automatically. Each event (user message, tool call, tool result, assistant response) is appended to the session's `events` list. When the Runner calls Gemini, it constructs the conversation from these events. Gemini 2.5 Flash has a 1M token context window, so in practice we rarely hit limits. However, if we needed to truncate, we could implement that logic inside `get_session` by only returning the last N events. The key difference is that ADK treats conversation as a sequence of typed events rather than raw message objects, which provides richer metadata (tool call IDs, function names, etc.) for the model's context.

---

## Tool Design

### Q7: How do ADK tools differ from LangChain tools, and what conventions does Gemini use to understand your tools?

**Answer:** In LangChain, tools are typically classes that inherit from `BaseTool` or functions decorated with `@tool`, requiring explicit `name`, `description`, and `args_schema` (a Pydantic model). In ADK, tools are plain Python `async` functions. Gemini reads the function name, parameter names, type hints, and the docstring to construct its internal tool schema. For example, our `get_customer_by_id(customer_id: str) -> dict` tool has a docstring that says "Fetches customer details by ID from BU1 onboarding service." Gemini sees the parameter `customer_id: str` and knows to extract a customer ID from the user's query. No decorators, no Pydantic schema for tool arguments, no registration boilerplate. The convention is: use descriptive function names (Gemini reads them), type-hint every parameter, and write a clear docstring explaining what the tool does and what it returns. The Agent constructor simply takes a list of these functions: `tools=[get_customer_by_id, search_onboarding_docs, ...]`.

### Q8: Your CRUD tools like `get_customer_by_id` use httpx to call microservices. How does parameter extraction work when the user says "look up customer C-101"?

**Answer:** Gemini's function-calling mechanism extracts parameters from natural language. When the user says "look up customer C-101", Gemini sees that `get_customer_by_id` takes `customer_id: str` and the docstring mentions "customer ID". It generates a function call with `customer_id="C-101"`. The Runner then invokes our async function, which makes an `httpx.AsyncClient().get(f"{_BASE_URL}/customers/{customer_id}")` call to the BU1 microservice. The response dict is returned to the Runner, which passes it back to Gemini as the tool result. Gemini then synthesizes a human-readable response from the raw JSON. This is powerful because we never write parsing logic -- Gemini handles entity extraction from the query, maps it to the correct tool parameter, and formats the result for the user. For ambiguous queries, Gemini will ask a clarifying question rather than guessing.

### Q9: How do you handle tool errors? For instance, what happens if a customer ID is not found?

**Answer:** Each tool function handles errors at the HTTP level. For example, `get_customer_by_id` checks `if response.status_code == 404: return {"error": f"Customer '{customer_id}' not found"}`. It returns an error dict rather than raising an exception. This is intentional -- if we raised an exception, the Runner would need to catch it and the model would not have context about what went wrong. By returning `{"error": "..."}`, the error message flows back to Gemini as the tool result, and Gemini can then tell the user "Customer C-101 was not found in the onboarding system" in natural language. For unexpected errors (network timeouts, 500s), `response.raise_for_status()` will raise an `httpx.HTTPStatusError`. The Runner catches unhandled tool exceptions and surfaces them to the model as error events, so the conversation does not break -- Gemini will typically respond with "I encountered an error trying to fetch that information."

---

## RAG Pipeline

### Q10: Describe the two-stage retrieval pipeline (vector search + cross-encoder re-ranking) and why you use it.

**Answer:** The pipeline works in two stages. First, MongoDB Atlas Vector Search performs approximate nearest neighbor (ANN) search using the query embedding against stored chunk embeddings. We over-fetch by requesting `limit: top_k * 3` results (e.g., 15 chunks when we want 5), with `numCandidates: top_k * 10` (e.g., 50) to give the ANN algorithm a larger candidate pool for better recall. Second, we pass these 15 candidate chunks through a cross-encoder re-ranker (`ms-marco-MiniLM-L-6-v2`). The cross-encoder takes each (query, chunk) pair and produces a relevance score using cross-attention -- unlike bi-encoder embeddings that compare vectors independently, the cross-encoder jointly attends to both texts, catching semantic nuances that embedding similarity misses. We sort by re-rank score and return the top_k. This two-stage approach gives us the speed of ANN search (sub-100ms for millions of vectors) plus the precision of cross-attention re-ranking (which would be too slow to run over the entire collection but is fast on 15 candidates).

### Q11: Explain the `$vectorSearch` aggregation pipeline stage used in MongoDB Atlas. What are `numCandidates` and `limit`?

**Answer:** The `$vectorSearch` stage is a MongoDB Atlas-specific aggregation operator that performs ANN search on a vector index. In our code, the pipeline is:
```python
{"$vectorSearch": {
    "index": "vector_index",
    "path": "embedding",
    "queryVector": query_vector,
    "numCandidates": top_k * 10,
    "limit": top_k * 3
}}
```
`index` is the name of the Atlas Vector Search index defined on the collection. `path` is the field containing the embedding array. `queryVector` is the embedding of the user's query. `numCandidates` tells the ANN algorithm how many candidates to consider internally -- higher values improve recall at the cost of latency. `limit` is how many results to return. The followed `$project` stage computes `{"$meta": "vectorSearchScore"}` which returns the cosine similarity score. We also support optional pre-filters: in BU5's `VectorDAO`, we pass `filter: {"metadata.service_type": service_type}` to narrow results to a specific care type (e.g., "physical-therapy") before the vector search runs. This filter must use fields included in the vector index definition as `filter` fields.

### Q12: Why did you choose tiktoken's `cl100k_base` encoding for chunking instead of character-based splitting?

**Answer:** Character-based splitting (e.g., split every 2000 characters) is unpredictable because different languages, code blocks, and whitespace patterns produce wildly different token counts for the same character length. Since both the embedding model and the LLM operate on tokens, we want chunks of consistent token size. We use `tiktoken.get_encoding("cl100k_base")` which is the BPE tokenizer used by GPT-4 and is a reasonable approximation for Gemini's tokenizer. Our chunker encodes the full text into tokens, then creates sliding windows of 500 tokens with 50-token overlap. The overlap ensures that sentences split at chunk boundaries still have context in both adjacent chunks, improving retrieval accuracy. The 500-token chunk size is a sweet spot: small enough for precise retrieval (a chunk about one specific topic) but large enough to contain meaningful context.

### Q13: You mentioned section-based chunking for care documents. How does that differ from the default token-based approach?

**Answer:** For BU5 care documents, each document describes care preparation for a specific body part or service type (e.g., "Hip Replacement Care", "Shoulder Physical Therapy"). These documents have natural section boundaries. Instead of blindly splitting by token count (which might cut a "Required Equipment" section in half), section-based chunking preserves the semantic integrity of each section. Each body-part or procedure section becomes its own chunk with metadata tagging the `service_type`. This means when a field officer claims a hip-replacement visit, the vector search with `filter: {"metadata.service_type": "hip-replacement"}` returns the complete, coherent care instructions for that specific procedure rather than a random 500-token slice that might start mid-sentence in an unrelated section. The token-based chunker is still used for general documents (onboarding policies, billing statements, service manuals) where there are no predictable section boundaries.

---

## Gemini Embedding Model

### Q14: Compare the Gemini embedding model (gemini-embedding-001) with OpenAI's text-embedding-3-small. What are the key differences?

**Answer:** Gemini-embedding-001 produces 3072-dimensional vectors, compared to OpenAI's text-embedding-3-small at 1536 dimensions (or text-embedding-3-large at 3072). Higher dimensionality generally captures more nuanced semantic relationships. The Google GenAI client provides a simpler API: `client.models.embed_content(model="gemini-embedding-001", contents=batch)` returns embeddings directly, supporting batch input as a list of strings. The batch limit is 100 texts per call, which we handle by looping in our embedder: `for i in range(0, len(chunks), BATCH_SIZE)`. Both models use cosine similarity for comparison. A practical advantage is that using Gemini embeddings alongside Gemini 2.5 Flash for the agent keeps us within one API key and billing account (Google AI), rather than splitting between OpenAI for embeddings and Google for the LLM. The ARCHITECTURE.md references 1536 dimensions from the earlier OpenAI version, but the current implementation uses gemini-embedding-001 with 3072 dimensions.

### Q15: How do you handle the embedding API's batch size limit of 100 in the ingestion pipeline?

**Answer:** In the `embedder.py` module, we define `BATCH_SIZE = 100` and loop through chunks in batches:
```python
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i : i + BATCH_SIZE]
    response = client.models.embed_content(model="gemini-embedding-001", contents=batch)
    all_embeddings.extend([e.values for e in response.embeddings])
```
This is important because the Google GenAI API rejects requests with more than 100 texts. If we have 350 chunks, we make 4 API calls (100 + 100 + 100 + 50). Each embedding is a list of 3072 floats. After embedding, we zip chunks with their embeddings and attach metadata (BU, customer_id, chunk_index, optional service_type) into the document format that gets inserted into MongoDB. Note that in the ingestion DAG (Airflow), this runs synchronously since Airflow tasks use the sync Google GenAI client, while in the agent's RAG tools we use the async client (`client.aio.models.embed_content`).

---

## MongoDB Atlas Vector Search

### Q16: How is the vector index configured in MongoDB Atlas, and what fields does it cover?

**Answer:** Each BU has its own collection (e.g., `bu1_document_chunks`, `bu5_document_chunks`) with a vector index named `vector_index`. The index is created in Atlas's UI or via the Atlas Admin API, specifying the `embedding` field as a vector field with 3072 dimensions and cosine similarity. For BU5, the index also includes `metadata.service_type` as a filter field, allowing pre-filtered vector search. The document schema is: `{ text: string, embedding: [float * 3072], metadata: { bu: string, customer_id: string, chunk_index: int, service_type?: string } }`. The `$vectorSearch` stage requires this index to exist before queries can run. The `numCandidates` parameter (set to `top_k * 10`) controls how many internal candidates the HNSW (Hierarchical Navigable Small World) graph algorithm examines -- Atlas uses HNSW under the hood for approximate nearest neighbor search.

### Q17: How does the cross-BU `search_all_bus` function work, and why is it parallelized?

**Answer:** The `search_all_bus` function in `rag_tools.py` searches all five BU vector collections simultaneously using `asyncio.gather`. For each BU collection, it calls `_search_collection` which runs the `$vectorSearch` pipeline. Since these are independent database queries against different collections, they can execute in parallel, reducing wall-clock time from ~5x a single query to roughly ~1x. The results from all BUs are flattened into a single list, sorted by vector search score, then the top `k * 3` candidates are passed through the cross-encoder re-ranker, and finally the top `k` results are returned. Each result carries a `bu` label so the agent can cite which business unit the information came from. This is the tool Gemini uses when a query could span multiple BUs -- for example, "What are the standard procedures across all departments for handling a new customer?"

---

## Cross-Encoder Re-ranking

### Q18: Why use a cross-encoder for re-ranking instead of just relying on vector similarity scores?

**Answer:** Bi-encoder embeddings (what we use for vector search) encode the query and each document independently into fixed vectors, then compare with cosine similarity. This is fast but lossy -- the representations are computed without seeing each other, so subtle semantic relationships are missed. A cross-encoder like `ms-marco-MiniLM-L-6-v2` takes the (query, document) pair as a single input and applies cross-attention, allowing every token in the query to attend to every token in the document. This captures nuances like negation, specificity, and contextual relevance that cosine similarity over independent embeddings cannot. However, cross-encoders are O(n) in the number of candidates and much slower per-pair, so we cannot run them over the entire collection. The two-stage approach gives us the best of both worlds: vector search for fast recall over the full collection, cross-encoder for precise ranking over a small candidate set.

### Q19: What is the over-fetch strategy, and how did you determine the multipliers (top_k * 3 for limit, top_k * 10 for numCandidates)?

**Answer:** The over-fetch strategy acknowledges that ANN search is approximate and the top results by vector similarity are not necessarily the most relevant. We set `numCandidates = top_k * 10` to give MongoDB's HNSW algorithm a larger search space (more graph nodes to explore), improving recall. We set `limit = top_k * 3` to retrieve three times more results than we ultimately need, giving the cross-encoder a richer candidate pool to re-rank. The multipliers are empirically tuned: 10x numCandidates is Atlas's recommended starting point (their docs suggest 10-20x for good recall). The 3x limit for re-ranking is a balance -- too few candidates and the re-ranker cannot improve much; too many and re-ranking latency increases (MiniLM-L-6-v2 runs ~1ms per pair, so 15 pairs is ~15ms, acceptable). In the cross-BU `search_all_bus`, we further trim: we take the top `k * 3` from the merged results before re-ranking, so the re-ranker never sees more than 15 documents even when searching all five collections.

---

## Traefik API Gateway

### Q20: Why Traefik over Nginx or Kong, and how does Docker label-based auto-discovery work?

**Answer:** Traefik was chosen for three reasons: (1) zero-config service discovery via Docker labels -- when a new container starts with `traefik.enable=true`, Traefik automatically registers it as a backend without touching any configuration file; (2) native Docker Compose integration -- it reads the Docker socket (`/var/run/docker.sock`) to watch for container events; (3) built-in middleware like `stripPrefix` that we need for our URL routing. Each BU service has labels like:
```yaml
- "traefik.http.routers.bu1.rule=PathPrefix(`/bu1`)"
- "traefik.http.middlewares.bu1-strip.stripprefix.prefixes=/bu1"
- "traefik.http.routers.bu1.middlewares=bu1-strip"
- "traefik.http.services.bu1.loadbalancer.server.port=8001"
```
When a request hits `http://gateway/bu1/customers/C-101`, Traefik matches the `/bu1` prefix, strips it (so the backend sees `/customers/C-101`), and forwards to port 8001 of the BU1 container. Nginx would require a static config file that must be rebuilt every time a service is added. Kong is more feature-rich but heavier -- overkill for our internal-only gateway.

### Q21: Explain the `root_path` setting on FastAPI and why it is needed behind Traefik's stripPrefix.

**Answer:** When Traefik strips the `/bu1` prefix, the FastAPI app at port 8001 receives requests at `/customers/...` and has no knowledge that externally its paths are prefixed with `/bu1`. This becomes a problem for Swagger UI: FastAPI generates its OpenAPI schema with paths like `/customers/{id}`, but when you access the docs at `http://gateway/bu1/docs`, the "Try it out" button sends requests to `/customers/{id}` (without the `/bu1` prefix), which Traefik cannot route. Setting `root_path="/bu1"` on FastAPI tells it "my externally visible base path is `/bu1`". FastAPI then generates the OpenAPI schema with `servers: [{url: "/bu1"}]`, so Swagger UI correctly prepends `/bu1` to all requests. This is a standard ASGI feature (`root_path` maps to the ASGI scope's `root_path`). Every BU service sets this: `FastAPI(root_path="/bu1")`, `FastAPI(root_path="/bu2")`, etc.

---

## Kafka Event-Driven Flow

### Q22: Explain the Kafka setup using KRaft mode. Why no Zookeeper?

**Answer:** Apache Kafka traditionally required Zookeeper for metadata management (broker registration, topic metadata, leader election). Starting with Kafka 3.3+, KRaft (Kafka Raft) mode replaces Zookeeper with an internal Raft-based consensus protocol. In our `docker-compose.yml`, the Kafka container runs with `KAFKA_PROCESS_ROLES: "broker,controller"` -- this single node acts as both the data broker and the Raft controller. `KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"` defines the Raft quorum (just one voter in our single-node setup). KRaft eliminates the operational overhead of running a separate Zookeeper ensemble, reduces the container count, simplifies the Docker Compose setup, and removes a potential failure point. The trade-off is that KRaft is newer and some older Kafka tooling may not support it, but for our use case (single topic, single consumer group, moderate throughput) it is perfectly stable.

### Q23: Walk through the complete appointment booking flow from the API call to the Slack DM with care instructions.

**Answer:** The flow has six steps: (1) A client POSTs to `POST /appointments` on the `appointment_service`. The handler generates a UUID for the appointment, constructs an event payload with `appointment_id`, `patient_id`, `patient_name`, `service_type`, `scheduled_at`, `address`, and `notes`. (2) The handler calls `producer.send_and_wait("appointment.booked", event)` using an `AIOKafkaProducer`, which publishes the event to the `appointment.booked` Kafka topic. (3) BU5's `AppointmentConsumer` (started during FastAPI lifespan as a background `asyncio.create_task`) is continuously polling Kafka. It deserializes the JSON message and calls `visit_service.handle_appointment_event(event)`. (4) The visit service creates a `Visit` document in MongoDB with status `PENDING`, then calls `slack_notifier.post_pending_visit(...)` which posts a Block Kit message to the `rc-care-members` Slack channel with a "Claim Visit" button. (5) A field officer clicks the button. Slack sends a `block_actions` event to the `slack_gateway` (via Socket Mode). The `handle_claim_action` handler PATCHes `BU5 /visits/{visit_id}/claim` with the user's Slack ID. (6) BU5's `claim_visit` method assigns the visit, performs a vector search for care instructions filtered by `service_type`, and returns the instructions. The slack_gateway updates the channel message to show "Claimed by @user" and DMs the officer with visit details and a care preparation checklist built from the RAG results.

### Q24: How does the aiokafka consumer integrate with FastAPI's async lifecycle?

**Answer:** In BU5's `main.py`, we use FastAPI's `lifespan` context manager. During startup (before `yield`), we create the `AppointmentConsumer`, call `await consumer.start()` to connect to Kafka, then launch `consume_task = asyncio.create_task(consumer.consume(visit_service.handle_appointment_event))`. This starts an infinite async loop (`async for msg in self._consumer`) that runs concurrently with FastAPI's request handling -- both share the same asyncio event loop. During shutdown (after `yield`), we cancel the consume task with `consume_task.cancel()` and call `await consumer.stop()`. The consumer's `consume` method catches `asyncio.CancelledError` to exit cleanly. This pattern is crucial: if we used a synchronous Kafka consumer, it would block the event loop and prevent FastAPI from serving HTTP requests. `aiokafka` is specifically designed for asyncio, using non-blocking I/O for all Kafka protocol operations.

---

## Slack Integration

### Q25: Why use Slack Bolt Socket Mode instead of the Events API with HTTP webhooks?

**Answer:** Socket Mode uses a WebSocket connection initiated by the bot rather than receiving HTTP POSTs from Slack. Three reasons: (1) No publicly routable URL needed -- the `slack_gateway` container connects outbound to Slack's WebSocket endpoint, so it works behind firewalls, NATs, and inside Docker networks without exposing ports. In our `docker-compose.yml`, the slack_gateway has no `labels` for Traefik and no published ports. (2) Simpler development -- no need to set up ngrok or a public HTTPS endpoint during local development. (3) Lower latency for interactive components -- button clicks (like "Claim Visit") are delivered immediately over the persistent WebSocket rather than waiting for Slack to POST to an HTTP endpoint with retry logic. The trade-off is that Socket Mode requires an app-level token (`SLACK_APP_TOKEN` starting with `xapp-`) in addition to the bot token, and it is limited to apps installed in a single workspace (not distributed through the Slack App Directory).

### Q26: Explain the channel-to-BU mapping in the slack_gateway and why it skips intent classification.

**Answer:** The `channel_router.py` defines a `CHANNEL_BU_MAP` dictionary mapping Slack channel names to BUs:
```python
CHANNEL_BU_MAP = {
    "rc_help_customer_profile_backoffice": "BU1",
    "rc_help_sales_backoffice": "BU2",
    "rc_help_billing_fulfillment_backoffice": "BU3",
    "rc_help_support_backoffice": "BU4",
    "rc_care_members": "BU5",
}
```
When a message arrives in `rc_help_billing_fulfillment_backoffice`, the gateway sets `bu_hint="BU3"` in the payload sent to the agent. This gives Gemini a strong signal about which BU the query relates to, effectively bypassing the need for the model to infer the BU from the query text alone. This is an optimization -- back-office staff in the billing channel are almost always asking billing questions, so we can guide the model to prioritize BU3 tools. The agent still has access to all tools, so if someone in the billing channel asks about a customer's onboarding status, Gemini can still call BU1 tools. The `bu_hint` is a soft signal, not a hard constraint. The `is_watched` check ensures the bot only responds in these mapped channels and ignores messages in random channels it might be invited to.

---

## Microservice Communication

### Q27: How do the agent's tools communicate with the BU microservices, and why httpx over requests?

**Answer:** Each tool function in `ritecare_tools/tools/` creates an `httpx.AsyncClient()` and makes async HTTP calls to the BU microservices. For example, `get_customer_by_id` calls `await client.get(f"{_BASE_URL}/customers/{customer_id}")`. We use httpx rather than `requests` because the entire stack is async-first. The agent runs on asyncio (ADK's `runner.run_async`), FastAPI is async, Motor is async, aiokafka is async. Using the synchronous `requests` library would block the event loop during HTTP calls, preventing concurrent tool execution. With httpx, when Gemini requests two tools simultaneously, both HTTP calls execute concurrently on the event loop. The base URLs are configured via `pydantic-settings` and use Docker Compose service names for internal DNS (e.g., `http://bu1_onboarding:8001`). Each tool sets a reasonable timeout (10-15 seconds) to prevent hanging if a BU service is slow.

### Q28: What are the two communication patterns used in the system -- synchronous and asynchronous -- and when is each appropriate?

**Answer:** The system uses synchronous HTTP for request-response interactions (agent tools calling BU APIs, Slack gateway calling the agent API, ingestion service calling Airflow) and asynchronous Kafka messaging for fire-and-forget event-driven flows (appointment booking triggering care operations). The HTTP pattern is used when the caller needs an immediate response -- the agent needs the customer record to synthesize an answer, the Slack handler needs the agent's response to reply in the thread. The Kafka pattern is used for the appointment flow because: (a) the appointment_service does not need to wait for care operations to process the event -- booking confirmation is immediate; (b) decoupling allows BU5 to process events at its own pace and recover from failures independently; (c) if BU5 is temporarily down, events queue in Kafka and are consumed when it recovers (durability). A third pattern is the Airflow DAG trigger: the ingestion_service POSTs to Airflow's REST API to trigger a DAG run, then polls or receives a callback via the `notify` task -- this is async in the sense that ingestion is long-running and the initial API call returns immediately.

---

## Airflow Ingestion Pipeline

### Q29: Describe the Airflow DAG structure for document ingestion and how it is triggered.

**Answer:** The DAG `bu_ingestion` has five sequential tasks: `load >> chunk >> embed >> store >> notify`. It is configured with `schedule=None` meaning it only runs when triggered externally. The ingestion_service triggers it via Airflow's REST API: `POST /api/v1/dags/bu_ingestion/dagRuns` with a `conf` payload containing `file_path`, `bu`, `customer_id`, and optionally `service_type`. The `load` task reads the file (PDF via pypdf or plain text). The `chunk` task calls `chunk_document(text)` which uses tiktoken to split into 500-token chunks with 50-token overlap. The `embed` task calls `embed_chunks(chunks, bu, customer_id, service_type)` which batches chunks in groups of 100 and calls the Gemini embedding API. The `store` task uses PyMongo (synchronous, since Airflow tasks run in separate processes) to `insert_many` the embedded documents into the appropriate BU collection. The `notify` task POSTs back to the ingestion_service with `dag_run_id`, `bu`, `status`, and `chunks_stored`. Tasks pass data between them using XCom (Airflow's cross-communication mechanism) via `ti.xcom_push` and `ti.xcom_pull`.

### Q30: Why use Airflow for ingestion instead of handling it directly in the FastAPI service? What are the trade-offs?

**Answer:** Three reasons favor Airflow: (1) Observability -- each step (load, chunk, embed, store) is a visible task in the Airflow UI with logs, timing, retry counts, and status. If embedding fails for a large document, you can see exactly which task failed, inspect its logs, and re-run just that task without re-loading and re-chunking. (2) Retry and failure handling -- Airflow has built-in task retries with configurable backoff, alerting, and SLA monitoring. If the Google embedding API rate-limits us, the embed task retries automatically. (3) Separation of concerns -- the ingestion pipeline has different resource requirements (CPU for PDF parsing, network for embedding API, I/O for MongoDB bulk inserts) than the real-time API serving. Running it in Airflow isolates it from the request-serving path. The trade-offs are: (a) operational complexity -- running an Airflow scheduler and webserver adds containers and resource overhead; (b) latency -- triggering a DAG run and waiting for Airflow's scheduler to pick it up adds seconds of latency compared to processing inline; (c) XCom limitations -- Airflow XCom stores data in its metadata database (SQLite in our setup), so very large documents could cause issues. For production, we would switch to a PostgreSQL backend and consider storing chunks in a temporary file rather than XCom. The current setup uses `SequentialExecutor` (single-threaded) which is fine for moderate load but would need `CeleryExecutor` or `KubernetesExecutor` for parallel DAG runs.

---

## Security

### Q21b: How would you add JWT-based authentication to this architecture?

**Answer:** I would add a shared `auth` middleware that validates JWTs on every request. The flow would be: (1) An identity provider (e.g., Google Cloud Identity, Auth0) issues JWTs to authenticated users. (2) A FastAPI dependency (`Depends(verify_jwt)`) decodes the token, validates the signature against the provider's JWKS endpoint (cached), checks expiration, and extracts claims (user_id, roles, BU access). (3) For service-to-service calls (agent calling BU APIs), we would use service account tokens -- each service has its own credentials and requests a short-lived JWT scoped to the APIs it needs. (4) Traefik can be configured with a `forwardAuth` middleware that delegates authentication to a dedicated auth service before forwarding requests to backends. (5) Role-based authorization would check claims like `{"roles": ["bu1_admin", "bu3_viewer"]}` to restrict which BU APIs a user can access. Currently the system trusts the internal Docker network (all traffic is container-to-container), which is acceptable for development but not production.

---

## Error Handling and Observability

### Q22b: How do you handle errors across the distributed system, and what observability do you have?

**Answer:** Error handling operates at multiple layers: (1) Each BU service has custom exception handlers registered with FastAPI -- e.g., `CustomerNotFoundError` returns a 404 with a structured JSON body, `DuplicateCustomerError` returns 409. These use FastAPI's `app.add_exception_handler` pattern. (2) Tool functions in the agent catch HTTP errors and return error dicts rather than propagating exceptions, allowing Gemini to communicate failures gracefully. (3) The Kafka consumer wraps each message handler in a try/except to prevent a single bad event from crashing the consumer loop. (4) The Slack gateway catches agent API errors and responds with a user-friendly fallback message. For observability, we use `structlog` for JSON-formatted structured logging across all services, making logs parseable by log aggregation tools (ELK, CloudWatch). SlowAPI middleware on BU services provides rate limiting with configurable limits. For production, I would add OpenTelemetry tracing (propagating trace IDs from Traefik through the agent to BU services), Prometheus metrics on each FastAPI app (request counts, latencies, error rates), and health checks that docker-compose already uses to manage container restarts.

### Q23b: How would you scale this system for higher throughput?

**Answer:** Several scaling strategies apply: (1) Horizontal scaling of BU services -- Traefik's Docker provider automatically load-balances across multiple replicas of the same service (set `deploy.replicas: 3` in docker-compose). (2) The agent service is stateless (sessions are in MongoDB) so it scales horizontally. (3) Kafka partitioning -- partition the `appointment.booked` topic and run multiple BU5 consumer instances in the same consumer group for parallel event processing. (4) MongoDB Atlas auto-scales read throughput with secondary read preferences; write throughput scales with sharding. (5) The cross-encoder re-ranker is CPU-bound -- for high throughput, run it on a GPU or replace with a faster model like ColBERT. (6) Move Airflow to `CeleryExecutor` with Redis as broker for parallel DAG task execution. (7) Cache frequently queried embeddings and RAG results in Redis to avoid redundant embedding API calls. (8) For the Slack gateway, Socket Mode supports a single WebSocket connection per app instance, so high-volume Slack interactions would need the Events API with HTTP endpoints and horizontal scaling behind a load balancer.

---

## Session and Conversation Management

### Q24b: How does ADK's SessionService prevent concurrent writes from corrupting a session?

**Answer:** Our `MongoSessionService.append_event` uses MongoDB's atomic `$push` operator:
```python
await self.collection.update_one(
    {"id": session.id},
    {"$push": {"events": event.model_dump()}, "$set": {"state": session.state}},
)
```
`$push` is atomic at the document level in MongoDB -- even if two concurrent requests append events to the same session, each `$push` is applied atomically and no events are lost. However, there is a subtle race: if two requests read the session, both get the same event list, and both append locally before writing, the in-memory `session.events` list could be stale. In practice, the ADK Runner serializes event processing per session (it awaits each event before proceeding), so true concurrent writes to the same session are unlikely. For a production system with very high concurrency on the same session, we could use MongoDB change streams to keep the in-memory session synchronized, or use optimistic concurrency control with a version field.

### Q25b: What happens to session state when the agent container restarts?

**Answer:** Because sessions are persisted in MongoDB Atlas (not in memory), a container restart has zero impact on conversation state. When the restarted agent receives a request with an existing `session_id`, the `MongoSessionService.get_session` method loads the full session (including all previous events) from the `adk_sessions` collection. The Runner reconstructs the conversation history from these events and sends it to Gemini along with the new message. This is one of the primary motivations for implementing a custom `MongoSessionService` rather than using ADK's default `InMemorySessionService`. In a horizontally scaled deployment with multiple agent containers behind Traefik, any instance can serve any session because the state is externalized to MongoDB.

---

## Additional Architecture Questions

### Q26b: Why is the slack_gateway not behind Traefik, while all other services are?

**Answer:** The slack_gateway uses Socket Mode, which means it initiates an outbound WebSocket connection to Slack's servers -- it does not receive inbound HTTP requests from Slack. Therefore, there is no HTTP traffic to route through Traefik. The container does not publish any ports and has no Traefik labels in the docker-compose configuration. It communicates outbound to Slack (WebSocket) and outbound to the agent service and BU5 (HTTP via Docker's internal network). If we switched to the Slack Events API (HTTP webhooks), the gateway would need to be behind Traefik with a public-facing route. The comment in docker-compose explicitly notes this: `# Slack Gateway (outbound Socket Mode -- not behind Traefik)`.

### Q27b: How does pydantic-settings manage configuration across all services?

**Answer:** Each service has a `config.py` with a `Settings` class that inherits from `pydantic_settings.BaseSettings`. For example, the agent service's config defines `google_api_key: str`, `mongodb_uri: str`, `bu1_base_url: str`, etc. Pydantic-settings automatically reads values from environment variables (case-insensitive matching), with fallback to a `.env` file specified by `SettingsConfigDict(env_file=".env")`. In Docker Compose, environment variables are set per-service using `${VAR:-default}` syntax, pulling from the host's `.env` file or shell environment. This creates a clean configuration hierarchy: defaults in the Settings class, overrides from environment variables set in docker-compose, secrets from the `.env` file (not committed to git). Type validation happens at startup -- if `MONGODB_URI` is not set, the service fails immediately with a clear validation error rather than crashing later on the first database call.

### Q28b: Explain the rate limiting setup using SlowAPI on the BU services.

**Answer:** Each BU service integrates SlowAPI, which is a FastAPI-compatible rate limiter built on top of `limits`. In `main.py`, we see:
```python
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
```
The `limiter` object is configured separately (in `common/limiter/rate_limiter.py`) with rate limits like "100/minute" per IP or per API key. When a client exceeds the limit, SlowAPI raises `RateLimitExceeded`, which the registered handler converts to a 429 Too Many Requests response. This protects BU services from being overwhelmed by the agent making too many concurrent tool calls, runaway ingestion jobs, or external callers (if APIs are exposed). In production, you would configure the rate limiter to use Redis as a backend (instead of in-memory) so that rate limits are shared across multiple replicas of the same service.

### Q29b: How would the system handle a scenario where Gemini decides to call five tools in parallel -- one for each BU?

**Answer:** This is a strength of the ADK + async architecture. When Gemini issues five parallel function calls (e.g., one CRUD lookup per BU), the Runner invokes all five async tool functions concurrently. Each function creates its own `httpx.AsyncClient` and makes a non-blocking HTTP call to its respective BU service. Since these are all running on the same asyncio event loop, all five HTTP requests are in-flight simultaneously. The event loop multiplexes the I/O, and as responses arrive, the results are collected and sent back to Gemini in a single tool-results message. The total wall-clock time is roughly equal to the slowest BU response rather than the sum of all five. This is the same pattern used in `search_all_bus` with `asyncio.gather`, but here the concurrency is managed by the ADK Runner rather than explicit gather calls.

### Q30b: What monitoring would you add for the RAG pipeline specifically, and how would you detect retrieval quality degradation?

**Answer:** For RAG monitoring, I would track: (1) Embedding latency -- time to call the Gemini embedding API, alerting if it exceeds a threshold (e.g., >500ms). (2) Vector search latency -- time for the `$vectorSearch` aggregation to return, tracked per collection. (3) Re-ranker latency -- time for the cross-encoder to score candidates. (4) Retrieval relevance metrics -- log the vector search scores and re-rank scores for every query. If the average top-1 re-rank score drops below a threshold over time, it signals that either the queries are drifting (users asking questions the documents don't cover) or the embeddings are stale (documents have been updated but not re-embedded). (5) Hit rate -- percentage of queries where at least one result exceeds a minimum relevance score. (6) Chunk count monitoring -- track how many chunks are stored per BU collection. A sudden drop could indicate an ingestion failure; excessive growth could mean duplicate ingestion. For automated quality checks, I would periodically run a set of golden queries with known expected results and compare the retrieved chunks against ground truth, flagging when precision/recall drops below acceptable thresholds.
