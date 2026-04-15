# RiteCare Field Service Document Intelligence — Interview Q&A

---

## Architecture & Design

---

**Q1. You have 5 microservices communicating with each other. How did you decide what belongs in each service vs what should be shared?**

Each service owns a single business domain — customer onboarding (BU1), sales/maintenance (BU2), billing (BU3), support (BU4), care operations (BU5). The boundary follows the bounded context principle from Domain-Driven Design. A service owns its own MongoDB collections, its own vector index, and its own ingestion metadata. Nothing is shared at the data layer. Communication happens only through HTTP APIs or Kafka events — never by sharing a database. The agent service is intentionally separate because it orchestrates across all BUs without owning any domain data itself.

---

**Q2. Why did you choose an event-driven approach (Kafka) for appointment booking instead of a direct REST call from appointment_service to bu5?**

A direct REST call would couple the two services — if BU5 is down, the appointment booking fails. With Kafka, the appointment_service publishes the event and returns immediately regardless of BU5's state. BU5 consumes the event when it is ready. This gives us temporal decoupling — the producer and consumer do not need to be running at the same time. It also makes it easy to add other consumers in the future (e.g. a billing service that needs to know about appointments) without changing the producer.

---

**Q3. The agent service calls BU1-BU5 services via HTTP. What are the trade-offs of this vs the agent directly accessing MongoDB?**

Direct MongoDB access would be faster and simpler but would couple the agent to every service's data model. If BU3 changes its schema, the agent breaks. By calling service APIs, the agent only depends on the API contract. Each BU service owns its own data model and exposes only what it wants to expose. The trade-off is latency — each tool call is a network hop. For this use case that is acceptable because the agent is already doing an LLM call which dominates the latency.

---

**Q4. You have both synchronous (HTTP) and asynchronous (Kafka) communication in the same system. How do you decide which to use?**

Use synchronous HTTP when the caller needs the result immediately to continue — e.g. a field officer asks a question and needs an answer in the same Slack thread. Use async Kafka when the action can be processed independently of the caller's flow — e.g. a patient books an appointment and the visit creation can happen in the background. The rule of thumb is: if the user is waiting for the response, use HTTP. If it is a side effect that can happen eventually, use Kafka.

---

**Q5. If bu5_care_operations goes down while Kafka has unprocessed appointment events, what happens when it comes back up?**

Kafka retains messages on the broker until they are committed by the consumer. BU5 uses `auto_offset_reset="earliest"` and a named consumer group `bu5-care-operations`. When BU5 restarts, it reconnects to the group and resumes from the last committed offset — so no messages are lost. The consumer commits offsets after successfully processing each message, not before, which means a crash mid-processing will cause the message to be reprocessed. This means `handle_appointment_event` should be idempotent — inserting a visit with the same `appointment_id` twice should not create duplicates. A guard using `appointment_id` as a unique index in MongoDB would handle this.

---

## LangGraph & AI Agent

---

**Q6. Explain the 3-node LangGraph pipeline. Why is it split into intent_classifier → tool_executor → responder instead of one single LLM call?**

Each node has a single responsibility. The intent_classifier decides routing — which BU and whether to use CRUD tools, RAG tools, or both. The tool_executor runs those tools in parallel and collects results. The responder synthesises the results into a natural language answer. Splitting them makes each node independently testable and replaceable. The classifier could be swapped for a rules-based router without touching the executor or responder. If we used one monolithic LLM call, we would lose this modularity and the ability to run tools outside the LLM's context window.

---

**Q7. The intent classifier uses an LLM to decide which BU to route to. What are the failure modes and how would you make it more reliable?**

Failure modes include: the LLM returning an unexpected format breaking the parser, misclassifying ambiguous queries, and latency adding to response time. To make it more reliable: enforce strict output format with few-shot examples in the prompt, add a fallback parser that handles malformed output gracefully, add retry logic with exponential backoff, and — as discussed — replace it with deterministic channel-to-BU mapping for Slack traffic so the LLM is only called for genuinely ambiguous multi-channel queries.

---

**Q8. You discussed replacing the intent classifier with channel-based routing. What are the trade-offs between deterministic routing vs LLM-based routing?**

Deterministic routing is fast, free, predictable, and never hallucinates. It works perfectly when the entry point already carries enough context — a Slack channel name tells you exactly which BU the user is operating in. LLM-based routing handles ambiguity and cross-BU queries naturally but adds latency, cost, and unpredictability. The right answer is to use both — deterministic routing as the primary path for known channels, LLM classification as a fallback for unmapped or multi-BU entry points.

---

**Q9. What is conversation history trimming with `trim_messages` and why is it necessary?**

Every LLM has a context window limit measured in tokens. If you include the full conversation history in every request, long conversations will eventually exceed this limit and fail. `trim_messages` with `strategy="last"` and `start_on="human"` keeps only the most recent messages that fit within `max_history_tokens`, always starting from a human turn so the context is coherent. Without trimming, the service would throw an error for long conversations. With trimming, older context is dropped but the conversation continues to work.

---

**Q10. The agent calls multiple BU tools in parallel for multi-BU queries. How does LangGraph's state management handle concurrent tool results?**

The tool_executor uses `asyncio.gather` to call multiple tool functions concurrently. Each call returns a result dict with `tool`, `bu`, `type`, and `result`. These are collected into a list and written back to the `tool_results` field in the AgentState. LangGraph state is immutable within a node — the node returns a dict of updates which LangGraph merges into the state before passing it to the next node. There is no shared mutable state between parallel calls, so there are no race conditions.

---

## RAG & Vector Search

---

**Q11. Walk me through the full ingestion pipeline from file upload to a searchable vector in MongoDB Atlas.**

A file is uploaded via `POST /ingest` on the ingestion_service. The orchestrator saves the file to a shared Docker volume and triggers an Airflow DAG run via the Airflow REST API, passing the file path, BU, and metadata in the DAG conf. The DAG runs five tasks sequentially: load (reads raw text from the file, handles PDF via pypdf), chunk (splits text into overlapping token-based chunks using tiktoken), embed (sends all chunks to OpenAI gemini-embedding-001 in a single batch call, gets 1536-dimensional vectors back), store (inserts documents with text, embedding, and metadata into the correct BU's MongoDB collection), and notify (POSTs completion status back to the ingestion_service which sends a Slack notification).

---

**Q12. Why do you use tiktoken for chunking instead of splitting by character count or sentence boundaries?**

LLM context limits and embedding model limits are measured in tokens, not characters. A character-based split might cut in the middle of a word when encoded, or create chunks that are too long for the embedding model. Tiktoken uses the same tokenizer as the target model (cl100k_base for gemini-embedding-001), so chunk sizes are accurate. Sentence boundary splitting is better than character splitting but ignores token budget. Token-based chunking with overlap ensures each chunk fits within the embedding model's limit while preserving semantic continuity across chunk boundaries.

---

**Q13. What is the significance of `numCandidates` in the MongoDB Atlas Vector Search pipeline?**

`numCandidates` controls how many candidate vectors Atlas considers before ranking and returning the top `limit` results. Atlas Vector Search uses an approximate nearest neighbour algorithm (HNSW). A higher `numCandidates` means a broader search — more accurate results but slower. A lower value is faster but may miss relevant documents. Setting `numCandidates` to `top_k * 10` is a common heuristic that balances recall and speed. If set too low, you may get poor results even though relevant documents exist in the collection.

---

**Q14. You added a `service_type` filter field to the BU5 vector index. How does pre-filtering differ from post-filtering in vector search?**

Pre-filtering (what MongoDB Atlas Vector Search does) applies the filter inside the ANN search itself — only documents matching `metadata.service_type == "skilled-nursing"` are considered as candidates. This is accurate and efficient. Post-filtering would run the vector search across all documents and then discard non-matching results — this wastes candidates on irrelevant documents and can return fewer than `top_k` results after filtering. Pre-filtering requires the filter field to be declared in the index definition, which is why we added `service_type` as a filter field when creating the Atlas index.

---

**Q15. If a field officer asks a vague question with no service type mentioned, how does your RAG handle it?**

The `service_type` filter is optional — if `_find_service_type` returns `None`, the search runs without a filter across all BU5 documents. The vector similarity alone determines relevance. This is correct behaviour for vague queries. To improve it, we could expand the query using the LLM before embedding (HyDE — Hypothetical Document Embedding), or use the visit's known service type from the conversation context as an implicit filter when the session is tied to a specific visit.

---

## Kafka

---

**Q16. Why does BU5 use `auto_offset_reset="earliest"` in its Kafka consumer?**

`earliest` means that when a consumer group connects to a topic for the first time (no committed offset yet), it starts reading from the beginning of the topic — so no messages published before the consumer started are missed. `latest` would mean the consumer only reads messages published after it connects, which would cause missed events if BU5 was down when appointments were booked. For event-driven systems where every event must be processed, `earliest` is the safe default.

---

**Q17. What is a consumer group ID and why does BU5 use `bu5-care-operations` as its group ID?**

A consumer group ID identifies a group of consumers that share the work of consuming a topic. Kafka tracks the committed offset per group — so each group has its own independent read position. Using a named group ID `bu5-care-operations` means that even if BU5 restarts, it resumes from where it left off. If we used a random UUID as the group ID, every restart would create a new group and either re-read all messages or miss old ones depending on `auto_offset_reset`. A stable group ID is essential for reliable exactly-once-ish processing.

---

**Q18. If the BU5 Kafka consumer crashes mid-processing of a message, will that message be lost or reprocessed?**

Reprocessed. By default, aiokafka commits offsets automatically after the message is returned to the consumer — but only after the message is fully yielded by the `async for` loop. If the handler crashes before the loop moves to the next message, the offset is not committed and the message will be redelivered on restart. This means handlers should be idempotent. For appointment events, the guard is to check whether a visit with the same `appointment_id` already exists in MongoDB before inserting.

---

**Q19. The appointment_service publishes and immediately returns a response. What are the consistency trade-offs?**

This is an eventually consistent pattern. The appointment_service confirms the booking to the caller as soon as the Kafka publish succeeds — but the visit in BU5's database may not exist yet. If the caller immediately queries BU5 for the visit, they may get a 404. This is acceptable for this use case because there is no expectation of immediate read-after-write consistency across services. The Slack notification to the members channel serves as the signal that the visit is ready. If Kafka is temporarily unavailable, `send_and_wait` will raise an exception and the caller gets a 500 — the appointment is not booked.

---

**Q20. How would you scale the BU5 consumer to handle high volume?**

Kafka scales consumers through partitions. Currently the `appointment.booked` topic has one partition, so only one consumer instance can read from it at a time. To scale: increase the topic partition count (e.g. to 5), then run multiple BU5 instances — each will be assigned a subset of partitions by Kafka's group coordinator. In Docker Compose this means `docker compose up --scale bu5_care_operations=5`. In Kubernetes this would be a horizontal pod autoscaler. Each instance processes its partition independently with no coordination needed.

---

## FastAPI & Microservices

---

**Q21. You follow a strict api → service → dao layering pattern. What does each layer own?**

The api layer owns HTTP concerns — request parsing, response serialisation, route definitions, rate limiting, and dependency injection. It knows nothing about business logic. The service layer owns business logic — validation, orchestration of multiple DAO calls, domain rules like "a visit can only be claimed if it is in PENDING status". It knows nothing about HTTP or MongoDB. The dao layer owns data access — MongoDB queries, document mapping, index usage. It knows nothing about business rules. This separation means you can swap MongoDB for PostgreSQL by only changing the DAO layer, and you can change business rules without touching routes.

---

**Q22. The BU5 lifespan starts a Kafka consumer as an asyncio background task. What are the risks?**

If the background task raises an unhandled exception, it silently dies — the FastAPI app continues serving HTTP requests but the Kafka consumer stops. The `consume` method catches `CancelledError` cleanly but only logs other exceptions and continues to the next message. For production, the task should be monitored with a health check that verifies the consumer is still running, and the task should have a restart mechanism. In Kubernetes, a liveness probe on the consumer could trigger pod restart.

---

**Q23. You use `slowapi` for rate limiting. Where in the stack does rate limiting belong?**

Ideally at the API gateway level (e.g. Kong, AWS API Gateway) so it is enforced before requests reach any service. Service-level rate limiting with slowapi is a second line of defence — useful for protecting individual services from internal callers that misbehave, or when there is no gateway. For this project, service-level rate limiting is appropriate since there is no dedicated gateway. In production, both layers together give the best protection.

---

**Q24. All services use `uv` with a locked `uv.lock` file. Why is a lock file critical for Docker builds specifically?**

Without a lock file, `uv sync` resolves the latest compatible versions at build time. This means two Docker builds on different days can produce images with different dependency versions — a subtle version bump in a transitive dependency could break the build or introduce a bug in production. The lock file pins every dependency including transitive ones to exact versions, so the build is fully reproducible. The Dockerfile uses `uv sync --no-dev` which installs exactly what is in the lock file, nothing more.

---

**Q25. How does FastAPI's `Depends()` system work and why is it better than instantiating DAOs directly inside route handlers?**

`Depends()` is FastAPI's dependency injection system. When a route is called, FastAPI inspects its function signature, resolves each `Depends()` by calling the dependency function, and injects the result. Dependencies can depend on other dependencies — `get_visit_service` depends on `get_visit_dao` which depends on `get_db`. This creates a lazy, per-request dependency graph with automatic lifecycle management. It is better than direct instantiation because: dependencies are easily swappable for tests (override with `app.dependency_overrides`), database connections are managed consistently, and there is no hidden shared state between requests.

---

## Slack & Real-time

---

**Q26. Why does your Slack gateway use Socket Mode instead of a webhook URL?**

Webhook mode requires a publicly accessible HTTPS URL — you need a domain, TLS certificate, and ingress. Socket Mode opens an outbound WebSocket connection from your server to Slack's infrastructure — no public URL needed. This is ideal for development and internal tools where exposing a public endpoint adds operational overhead. The trade-off is that Socket Mode requires an app-level token with `connections:write` scope and is not suitable for distributing apps to multiple Slack workspaces.

---

**Q27. When a field officer clicks "Claim Visit", Slack expects an acknowledgement within 3 seconds. How does your handler satisfy this?**

`await ack()` is called immediately at the start of `handle_claim_action`, before any HTTP call to BU5. This sends the acknowledgement to Slack instantly. All subsequent work — calling BU5, updating the message, opening a DM — happens after the ack. Slack Bolt's async runner executes the ack and the rest of the handler concurrently. If ack is not called within 3 seconds, Slack shows an error to the user even if the backend eventually completes successfully.

---

**Q28. The session key is `{channel_name}-{user_id}`. What problem does this solve?**

If the session key were just `user_id`, a field officer asking questions in two different channels would share conversation history across those channels. A question about a billing invoice in one channel would bleed into a sales contract discussion in another. By including the channel name, each channel gets its own isolated conversation history per user. This matches the mental model — the user is having separate conversations in separate contexts.

---

**Q29. A field officer asks the same question in two different channels. Should they get different answers?**

Yes, potentially. With channel-to-BU mapping, the same query in `rc_help_billing_fulfillment_backoffice` routes to BU3 and searches billing documents, while the same query in `rc_help_sales_backoffice` routes to BU2 and searches sales documents. The answer is scoped to the channel's domain. This is the correct behaviour — a field officer asking "what are the procedures?" means different things in a billing channel vs a care operations channel. Channel-to-BU mapping makes this implicit and automatic without requiring the user to specify the domain.

---

## Security & Production Readiness

---

**Q30. No auth exists between internal services. A new requirement says only field officers can claim visits and only admins can ingest documents. How would you implement this using Slack identity?**

Slack already authenticates the user via its HMAC request signature — we trust the `user_id` in the payload. The missing piece is a role mapping. Add a `users` collection in MongoDB: `{ slack_user_id, name, role }` where role is `field_officer` or `admin`. In `handle_claim_action`, before calling BU5, look up the user's role — if not `field_officer`, respond with an ephemeral "You are not authorised to claim visits" message and return. For ingestion, add the same check in the ingestion_service handler before accepting the upload. This avoids a separate login flow entirely — Slack is the identity provider for internal users, and MongoDB is the role store. For production, roles would be managed via Keycloak or Auth0 with Slack as a federated identity source.
