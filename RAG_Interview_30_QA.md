# 30 RAG Interview Questions — With Answers

---

## Fundamentals (1–10)

---

### 1. What is RAG and why does it exist? What problem does it solve over a standalone LLM?

RAG (Retrieval-Augmented Generation) is an architecture that combines an information retrieval step with an LLM generation step. Instead of relying solely on what the model memorized during training, RAG fetches relevant documents from an external knowledge base at query time and injects them into the LLM's prompt as context.

It solves several core LLM limitations:

- **Knowledge cutoff** — LLMs only know what was in their training data. RAG lets them answer questions about new or private information.
- **Hallucination** — without source material, LLMs may confidently fabricate facts. RAG grounds responses in retrieved documents.
- **Domain specificity** — a general-purpose LLM doesn't know your company's internal docs, policies, or data. RAG bridges that gap without fine-tuning.
- **Cost** — fine-tuning a model on new data is expensive and slow. RAG lets you update knowledge by simply updating the document store.

---

### 2. Walk me through the two main stages of a RAG pipeline — what happens at indexing time vs. query time?

**Indexing time (offline/batch):**

1. Load documents from sources (PDFs, databases, APIs, etc.).
2. Split documents into chunks (paragraphs, sentences, or fixed-size windows).
3. Generate an embedding vector for each chunk using an embedding model (e.g., OpenAI `gemini-embedding-001`, Cohere Embed, or an open-source model like `all-MiniLM-L6-v2`).
4. Store the vectors along with the original text and metadata in a vector database (Pinecone, Weaviate, Chroma, pgvector, etc.).

**Query time (online/per-request):**

1. Take the user's question and embed it using the same embedding model.
2. Search the vector database for the top-K most similar chunks (cosine similarity or dot product).
3. Optionally re-rank or filter the retrieved chunks.
4. Construct a prompt with the retrieved chunks as context + the user's question.
5. Send the prompt to the LLM and return the generated answer.

---

### 3. What are embeddings and why are they central to RAG? How does semantic similarity search work?

Embeddings are dense numerical vectors (e.g., 384 or 1536 dimensions) that represent the _meaning_ of a piece of text. Texts with similar meanings produce vectors that are close together in vector space, even if they use completely different words.

For example, "How do I reset my password?" and "I forgot my login credentials" would have very similar embedding vectors, even though they share almost no words.

Semantic similarity search works by:

1. Computing the embedding of the query.
2. Comparing it against all stored chunk embeddings using a distance metric — usually **cosine similarity** (measures the angle between vectors) or **dot product**.
3. Returning the chunks with the highest similarity scores.

This is what makes RAG powerful over keyword search — it understands _intent_, not just exact word matches.

---

### 4. What is a vector database? How does it differ from a traditional relational database?

A vector database is purpose-built for storing, indexing, and querying high-dimensional vectors efficiently. Key differences:

| Aspect     | Relational DB (PostgreSQL) | Vector DB (Pinecone, Weaviate)  |
| ---------- | -------------------------- | ------------------------------- |
| Data model | Rows and columns           | Vectors + metadata              |
| Query type | SQL (exact match, range)   | Nearest-neighbor similarity     |
| Indexing   | B-tree, hash               | HNSW, IVF, PQ                   |
| Strength   | Transactions, joins, ACID  | Fast similarity search at scale |

Popular options:

- **Managed:** Pinecone, Weaviate Cloud, Qdrant Cloud
- **Open source:** Chroma, Milvus, Qdrant, Weaviate
- **Extensions on existing DBs:** pgvector (PostgreSQL), Atlas Vector Search (MongoDB)

Note: pgvector blurs the line — you can do vector similarity search inside PostgreSQL alongside your regular relational data.

---

### 5. What is chunking? Why can't you just embed an entire document as one vector?

Chunking is the process of splitting documents into smaller pieces before embedding. You can't embed whole documents for several reasons:

- **Embedding models have token limits** — most max out at 512 or 8192 tokens. A 50-page PDF won't fit.
- **Diluted meaning** — a single vector for an entire document averages out all the topics, making it match many queries weakly rather than the right query strongly.
- **Precision** — if you retrieve an entire document, the LLM has to sift through pages of irrelevant content to find the answer. Small, focused chunks give the LLM exactly what it needs.
- **Context window limits** — the LLM can only accept so many tokens. Retrieving a few relevant chunks is more efficient than stuffing in whole documents.

---

### 6. What chunking strategies exist and when would you pick one over another?

**Fixed-size chunking:** Split every N tokens/characters with optional overlap. Simple, predictable, works well as a baseline. Risk: splits can land mid-sentence.

**Sentence-based:** Split on sentence boundaries. Respects linguistic units but individual sentences may lack context.

**Recursive/hierarchical:** Try splitting on paragraphs first, then sentences, then characters — using the largest unit that fits the size limit. LangChain's `RecursiveCharacterTextSplitter` does this. Good general-purpose choice.

**Semantic chunking:** Use the embedding model itself to detect topic shifts — start a new chunk when the embedding similarity between consecutive sentences drops. More compute-intensive but produces coherent topic-aligned chunks.

**Document-structure-aware:** Split on actual structural elements (headings, sections, markdown headers, HTML tags). Best for well-structured content like documentation or legal contracts.

When to pick what:

- Unstructured plain text → recursive
- Well-structured docs (markdown, HTML) → structure-aware
- High-precision needs → semantic
- Quick prototype → fixed-size with overlap

---

### 7. What does "grounding" mean in the context of RAG, and how does RAG reduce hallucination?

Grounding means tying the LLM's response to specific, verifiable source material rather than letting it generate from its parametric memory alone.

RAG reduces hallucination by:

1. **Providing evidence** — the LLM is given retrieved documents and instructed to answer _based on_ them, not from general knowledge.
2. **Constraining the output** — the prompt typically says "Answer only based on the provided context. If the answer isn't in the context, say so."
3. **Enabling verification** — because you know which chunks were retrieved, you can cite sources, letting users verify claims.

RAG doesn't eliminate hallucination completely. The LLM can still misinterpret context, or the retrieved chunks might not contain the answer (causing the LLM to guess anyway). But it dramatically reduces the problem compared to asking a bare LLM.

---

### 8. Explain the difference between keyword/sparse retrieval (like BM25) and dense/semantic retrieval. What is hybrid search?

**Sparse retrieval (BM25, TF-IDF):**

- Represents documents as sparse vectors where each dimension is a word.
- Matches based on exact keyword overlap (term frequency, inverse document frequency).
- Fast, interpretable, great when the user's query uses the exact same terminology as the documents.
- Fails when synonyms or paraphrases are used ("car" won't match "automobile").

**Dense retrieval (embeddings):**

- Represents documents as dense vectors (hundreds of dimensions) capturing semantic meaning.
- Matches based on meaning similarity, regardless of exact words used.
- Handles synonyms, paraphrases, and conceptual queries well.
- Can fail on exact keyword matches, rare terms, or IDs/codes that have no "meaning."

**Hybrid search:**

Combines both — run BM25 and vector search in parallel, then merge the results using Reciprocal Rank Fusion (RRF) or a weighted score. This gives you the best of both: semantic understanding + exact keyword precision. Most production RAG systems use hybrid search.

---

### 9. What role does the prompt template play in RAG? How do you structure the retrieved context and the user question for the LLM?

The prompt template is the glue between retrieval and generation. A typical structure:

```
You are a helpful assistant. Answer the user's question based ONLY on the
provided context. If the context doesn't contain the answer, say "I don't
have enough information to answer that."

Context:
---
{chunk_1}

Source: document_name.pdf, page 12
---
{chunk_2}

Source: policy_v3.docx, section 4.2
---

Question: {user_question}

Answer:
```

Key design decisions:

- **System instruction** — tells the LLM to stay grounded and not hallucinate.
- **Context formatting** — each chunk clearly delimited, optionally with source metadata for citation.
- **Chunk ordering** — most relevant first (or most relevant at start and end, to avoid "lost in the middle").
- **Explicit fallback** — telling the model what to do when context is insufficient prevents fabrication.

---

### 10. What are the typical evaluation metrics for a RAG system?

RAG evaluation splits into **retrieval quality** and **generation quality**:

**Retrieval metrics:**

- **Recall@K** — of all relevant chunks in the corpus, what fraction did we retrieve in the top K?
- **Precision@K** — of the K chunks we retrieved, how many were actually relevant?
- **MRR (Mean Reciprocal Rank)** — how high does the first relevant chunk appear in the results?
- **NDCG** — normalized discounted cumulative gain, accounts for ranking order.

**Generation metrics:**

- **Faithfulness** — does the answer only contain information from the retrieved context (no hallucination)?
- **Answer relevance** — does the answer actually address the question?
- **Context relevance** — were the retrieved chunks relevant to the question?
- **Correctness** — compared to a ground truth answer, is the response factually right?

**Frameworks for automated evaluation:**

- **RAGAS** — computes faithfulness, answer relevancy, context precision, context recall automatically using an LLM-as-judge approach.
- **DeepEval** — similar LLM-based evaluation suite.
- **Human evaluation** — still the gold standard, especially for nuanced or domain-specific answers.

---

## Intermediate (11–20)

---

### 11. What is the "lost in the middle" problem?

Research has shown that LLMs pay the most attention to information at the **beginning** and **end** of their context window, and tend to overlook content in the **middle**. This means if you retrieve 10 chunks and the most relevant one lands at position 5, the LLM might miss it.

**Mitigations:**

- **Put the most relevant chunks first** (sort by similarity score descending).
- **Use fewer, higher-quality chunks** rather than stuffing in many.
- **Place key chunks at both the beginning and end** of the context.
- **Re-rank** to ensure only the most relevant chunks are included.
- **Use models with better long-context handling** (newer models have improved at this).

---

### 12. Explain re-ranking. Why retrieve 20 chunks but re-rank to the top 5?

Initial vector search (bi-encoder) is fast but approximate — it encodes the query and each document independently, then compares vectors. This can miss nuances.

Re-ranking uses a **cross-encoder** — a model that takes the query and a candidate chunk _together_ as input and produces a more accurate relevance score. This is much more compute-intensive (you can't do it over millions of documents), but very accurate over a small candidate set.

**The two-stage pipeline:**

1. **Retrieve** — fast vector search returns top 20 candidates.
2. **Re-rank** — cross-encoder scores each of the 20, you keep the top 5.

This gives you the speed of vector search with the accuracy of cross-encoding.

**Tools:** Cohere Rerank, ColBERT, `cross-encoder/ms-marco-MiniLM` from Sentence Transformers, Jina Reranker.

---

### 13. What is HyDE (Hypothetical Document Embeddings)?

HyDE is a technique where instead of embedding the user's raw question for retrieval, you first ask the LLM to generate a **hypothetical answer** (without any context), then embed _that_ answer and use it for retrieval.

**Why it works:** A hypothetical answer is linguistically closer to how the actual documents are written than a short question is. Questions and answers live in different semantic spaces. "What is the refund policy?" (question) is less similar to a policy document than "The refund policy allows returns within 30 days..." (hypothetical answer).

**Trade-off:** It adds an extra LLM call per query (latency and cost), and the hypothetical answer might be wrong — but it just needs to be in the right semantic neighborhood, not factually correct.

---

### 14. How do metadata filters work in RAG?

Metadata filters let you narrow the search space _before_ doing vector similarity, combining structured filtering with semantic search.

**Example:** A legal RAG system with documents from multiple clients:

```python
results = vector_db.query(
    vector=query_embedding,
    filter={
        "client_id": "acme-corp",
        "document_type": "contract",
        "date": {"$gte": "2024-01-01"}
    },
    top_k=5
)
```

This ensures you only search ACME Corp's contracts from 2024 onward — no matter how semantically similar another client's documents might be.

**Critical use cases:**

- **Access control** — user A shouldn't retrieve user B's private documents.
- **Temporal relevance** — prefer recent policies over outdated ones.
- **Source filtering** — search only in specific document categories.
- **Multi-tenancy** — isolate data between different customers in a SaaS product.

Without metadata filters, vector search alone might return a highly similar chunk that the user shouldn't have access to or that's from an outdated source.

---

### 15. What is the difference between naive RAG, advanced RAG, and modular RAG?

**Naive RAG:**
The simplest pipeline: chunk → embed → retrieve → generate. No pre-processing, no re-ranking, basic prompt. Works for demos but struggles in production with noisy retrieval, irrelevant chunks, and hallucination.

**Advanced RAG:**
Adds improvements at each stage:

- **Pre-retrieval:** query rewriting, HyDE, step-back prompting.
- **Retrieval:** hybrid search, metadata filtering.
- **Post-retrieval:** re-ranking, context compression, deduplication.
- **Generation:** better prompts, chain-of-thought reasoning, citation enforcement.

**Modular RAG:**
Treats each component as a swappable module — retriever, re-ranker, reader, router, judge. You can mix and match, add routing logic ("does this query even need retrieval?"), multi-step retrieval, and feedback loops. This is the architecture behind most production systems and agentic RAG.

---

### 16. How do you handle multi-turn conversations in RAG?

The core problem: a follow-up like "Tell me more about that" or "What about the second one?" is meaningless as a standalone search query. The retriever has no idea what "that" refers to.

**Solutions:**

- **Query condensation/rewriting** — use the LLM to rewrite the follow-up into a standalone question given the chat history. Example: chat history says you discussed refund policies → "Tell me more" becomes "What are the details of the refund policy?"

```python
standalone_query = llm(f"""Given this conversation:
{chat_history}

Rewrite this follow-up as a standalone question:
"{follow_up_question}"
""")
```

- **Contextual compression** — summarize the conversation history and prepend it to the current query.
- **Conversation-aware embeddings** — embed the entire recent conversation, not just the last message.

Most production systems use query rewriting — it's the simplest approach that works reliably.

---

### 17. What is query transformation/rewriting?

The user's raw question is often a poor search query. Query transformation techniques rewrite it for better retrieval:

**Sub-question decomposition:** Break a complex question into simpler ones.

- "Compare the pricing and features of Plan A vs Plan B" → two queries: "What is the pricing of Plan A?" and "What are the features of Plan B?"

**Step-back prompting:** Ask a more general question first to get broader context.

- "Why did revenue drop in Q3 2024?" → "What were the key financial events in 2024?"

**Query expansion:** Add synonyms or related terms.

- "EKS migration issues" → "EKS migration issues, Kubernetes AWS problems, container orchestration errors"

**HyDE:** Generate a hypothetical answer and use it as the search query (covered in Q13).

**Multi-query:** Generate multiple rephrasings of the same question, retrieve for each, and merge results. Increases recall at the cost of more retrieval calls.

---

### 18. How do you handle tables, images, or structured data in RAG?

These are challenging because embedding models are trained primarily on prose text.

**Tables:**

- Convert to markdown or CSV format before chunking — preserves structure better than plain text extraction.
- Summarize each table with an LLM ("This table shows quarterly revenue by region for 2023–2024") and embed the summary. Store the original table as metadata to pass to the LLM at generation time.
- Use specialized table extraction tools (Camelot, Tabula, AWS Textract).

**Images:**

- Use a multi-modal embedding model (CLIP, OpenAI's multi-modal embeddings) that can embed both images and text into the same vector space.
- Use an LLM with vision (GPT-4V, Claude) to generate text descriptions of images, then embed those descriptions.
- For charts/diagrams, extract data or descriptions first.

**Structured data (JSON, SQL):**

- Convert to natural language summaries for embedding.
- Or use text-to-SQL: let the LLM write a SQL query against your database instead of doing vector search. This is a different pattern from vector RAG but falls under the RAG umbrella.

---

### 19. What is a context window limit and how does it constrain RAG?

The context window is the maximum number of tokens an LLM can process in a single call (prompt + response combined). For example, Claude Sonnet has a 200K token window, GPT-4o has 128K.

**How it constrains RAG:**

- You can only fit so many retrieved chunks into the prompt. If you retrieve 50 relevant chunks totaling 100K tokens, you might hit the limit.
- Longer contexts increase cost (you pay per token) and latency.
- Even with large windows, quality degrades with too much context ("lost in the middle").

**Strategies when context exceeds the limit:**

- **Retrieve fewer, higher-quality chunks** — re-rank and take only top 3–5.
- **Context compression** — use an LLM to summarize chunks before passing them to the generation step (called "compressive RAG").
- **Map-reduce** — process each chunk independently, then combine the answers.
- **Iterative retrieval** — retrieve a small set, generate a partial answer, then retrieve more if needed.

---

### 20. Explain the trade-off between chunk size and retrieval precision.

**Chunks too small (e.g., individual sentences):**

- High precision — each chunk is very focused.
- But loses context — a single sentence might not contain enough information to answer a question.
- Creates many more vectors to store and search.
- The LLM gets fragmented information that's hard to synthesize.

**Chunks too large (e.g., entire pages or sections):**

- Rich context — each chunk has enough information for a complete answer.
- But lower precision — the embedding averages out multiple topics, so the chunk might match queries about _any_ of those topics weakly.
- Wastes context window space — the LLM gets a lot of irrelevant text alongside the relevant bits.

**The sweet spot** is typically 200–500 tokens with 10–20% overlap between consecutive chunks. But this varies by use case — highly structured FAQ content works well with small chunks, while narrative legal documents need larger ones to preserve reasoning chains.

**Parent-child chunking** (see Q22) is a technique that gets the best of both: embed small chunks for precision, but retrieve the larger parent for context.

---

## Advanced (21–30)

---

### 21. What is agentic RAG?

Agentic RAG wraps the RAG pipeline inside an AI agent that can make decisions about _how_ to retrieve, _whether_ to retrieve, and _when to stop_.

Instead of the rigid retrieve-once-then-generate pattern, an agent can:

- **Decide if retrieval is needed** — "What's 2+2?" doesn't need a database lookup.
- **Choose which data source to query** — route to a vector DB for document questions, a SQL database for data questions, or a web search for current events.
- **Retrieve iteratively** — if the first retrieval doesn't answer the question, reformulate and try again.
- **Verify its own answer** — retrieve additional evidence to confirm or reject its draft response.
- **Use tools** — call APIs, run calculations, or execute code alongside retrieval.

**Example flow:**

```
User: "How does our Q3 revenue compare to the industry average?"

Agent thinks:
1. I need internal data → query vector DB for Q3 revenue docs
2. I need external data → web search for industry average
3. Combine both into a comparison
4. Generate answer with citations from both sources
```

Frameworks: LangGraph, Google ADK, CrewAI, AutoGen.

---

### 22. Explain parent-child chunking (sentence-window retrieval).

This technique solves the chunk-size trade-off by using **small chunks for retrieval** but **large chunks for generation**.

**How it works:**

1. Split a document into large "parent" chunks (e.g., full sections or pages).
2. Split each parent into smaller "child" chunks (e.g., individual sentences or small paragraphs).
3. Embed and index only the child chunks.
4. At query time, retrieve the most similar child chunks.
5. But instead of passing the child chunks to the LLM, look up their parent chunks and pass _those_ instead.

**Why it works:**

- Small child chunks are more precise — their embeddings are tightly focused on specific topics.
- Large parent chunks provide the surrounding context the LLM needs to give a complete answer.
- You get precision in retrieval + completeness in generation.

**Sentence-window retrieval** is a variant: embed individual sentences, but when a sentence matches, retrieve a window of N sentences around it (e.g., 2 before and 2 after).

---

### 23. What is Graph RAG?

Graph RAG builds a **knowledge graph** over your document corpus and uses graph-based retrieval instead of (or alongside) vector search.

**How it works:**

1. Extract entities and relationships from documents using an LLM (e.g., "Microsoft → acquired → GitHub", "Python → is-a → programming language").
2. Store them in a graph database (Neo4j, Amazon Neptune).
3. At query time, identify entities in the question, traverse the graph to find related entities and facts, and use those as context for the LLM.

**When it shines:**

- **Multi-hop questions** — "Who is the CEO of the company that acquired GitHub?" requires traversing: GitHub → acquired by Microsoft → CEO is Satya Nadella. Vector search struggles with this because no single chunk contains the full answer.
- **Global summarization** — "What are the main themes across all our customer complaints?" requires synthesizing across hundreds of documents. Graph RAG can pre-compute community summaries.
- **Relationship-heavy domains** — legal (clause references), biomedical (drug interactions), financial (entity ownership chains).

**Microsoft's GraphRAG** paper popularized this approach, using LLM-generated community summaries at different levels of the graph hierarchy.

---

### 24. How do you implement citation and attribution in RAG?

Citations let users verify that the answer comes from real sources. Implementation approaches:

**Approach 1: Prompt-based citation**

Include source identifiers in the context and instruct the LLM to cite them:

```
Context:
[Source A: benefits_policy.pdf, p.3] Employees receive 20 days PTO...
[Source B: handbook_v2.pdf, p.15] PTO accrues at 1.67 days per month...

Question: How much PTO do employees get?
Answer using [Source X] citations.
```

The LLM generates: "Employees receive 20 days of PTO [Source A], which accrues at 1.67 days per month [Source B]."

**Approach 2: Post-processing verification**

1. Generate the answer without citations.
2. For each claim in the answer, use an LLM or similarity search to find which chunk supports it.
3. Attach citations programmatically.

**Approach 3: Structured output**

Ask the LLM to return JSON with claims and their source IDs:

```json
{
  "answer": "Employees receive 20 days PTO...",
  "citations": [
    { "claim": "20 days PTO", "source_id": "A", "chunk_text": "..." }
  ]
}
```

**Key challenge:** LLMs sometimes "cite" the wrong source or fabricate a citation. Always validate that the cited chunk actually supports the claim.

---

### 25. What are PII/PHI guardrails in a RAG pipeline?

PII (Personally Identifiable Information) and PHI (Protected Health Information) guardrails prevent the RAG system from exposing sensitive data in its responses.

**Where to place guardrails:**

**Pre-retrieval:**

- Redact PII/PHI from documents _before_ indexing (names → [PERSON], SSNs → [REDACTED]).
- Apply access-control metadata filters so users only retrieve documents they're authorized to see.

**Post-retrieval:**

- Scan retrieved chunks for PII/PHI before passing to the LLM.
- Redact or mask sensitive fields in the chunks.

**Post-generation:**

- Scan the LLM's response for any PII/PHI that leaked through.
- Use regex patterns (SSN, phone, email) + NER models (names, addresses) to detect and redact.

**Defense in depth:** Apply guardrails at multiple stages — documents can be messy, and no single filter catches everything.

**Tools:** Microsoft Presidio, AWS Comprehend Medical, Google Cloud DLP, spaCy NER, custom regex patterns.

**In regulated industries (healthcare/HIPAA, finance):** This isn't optional — it's a legal requirement. The pipeline must be auditable, showing what data was retrieved and what was filtered.

---

### 26. How do you evaluate and detect retrieval failure vs. generation failure?

When the RAG system gives a wrong answer, the bug could be in retrieval or generation. Distinguishing them is critical for debugging:

**Retrieval failure — the right chunk was never retrieved:**

- Inspect the retrieved chunks manually. If none of them contain the answer, retrieval failed.
- Causes: bad chunking (answer split across chunks), poor embedding model, missing metadata filters, query-document vocabulary mismatch.
- Fix: improve chunking, try hybrid search, add query rewriting, use a better embedding model.

**Generation failure — the right chunk was retrieved but the LLM got it wrong:**

- The retrieved chunks contain the answer, but the LLM hallucinated, ignored it, or misinterpreted it.
- Causes: prompt template issues, "lost in the middle," chunk too long/noisy, ambiguous context, model limitations.
- Fix: improve prompt template, reduce context size, re-rank to put best chunk first, use a stronger model.

**Debugging workflow:**

1. Log every query along with: the retrieved chunks, their similarity scores, the full prompt sent to the LLM, and the generated answer.
2. For wrong answers, check: did the relevant chunk exist in the corpus? Was it retrieved? Where did it rank? Did the LLM's prompt contain it? What did the LLM do with it?
3. Build an evaluation dataset of question-answer-source triples and run automated scoring (RAGAS) to measure retrieval vs. generation quality separately.

---

### 27. What is fine-tuning an embedding model for RAG and when would you do it?

Fine-tuning an embedding model means training it on your domain-specific data so it produces better similarity scores for your particular use case.

**When off-the-shelf models fall short:**

- Your domain has specialized vocabulary (legal, medical, scientific) that general models don't encode well.
- You have a specific definition of "relevant" that differs from the model's default (e.g., in a legal context, "similar clauses" might mean something very precise).
- Your retrieval recall is low despite trying hybrid search, re-ranking, and query rewriting.

**What you need:**

- **Training data:** pairs of (query, relevant_document) and ideally (query, irrelevant_document) as negative examples. You can generate these from user click logs, QA pairs, or manually curated examples.
- **Typically 1,000–10,000 pairs** for meaningful improvement.
- A base model to fine-tune (e.g., `all-MiniLM-L6-v2`, `bge-base`, `e5-base`).

**Training approach:** Contrastive learning — push the query embedding closer to the relevant document embedding and farther from irrelevant ones. Libraries like Sentence Transformers make this straightforward.

**Trade-off:** Fine-tuned models can overfit to your domain and lose general capability. Always benchmark against the base model on a held-out test set.

---

### 28. How does RAG work with multi-modal content?

Multi-modal RAG retrieves from a corpus containing text, images, tables, diagrams, and other non-text content.

**Approaches:**

**1. Convert everything to text:**

- Use vision models to caption images and describe diagrams.
- Use OCR + table extractors for scanned documents.
- Embed the text descriptions alongside regular text chunks.
- Limitation: loses visual information that's hard to describe in words.

**2. Multi-modal embeddings (unified vector space):**

- Use models like CLIP, OpenCLIP, or Voyage multimodal that embed both text and images into the same vector space.
- A text query can retrieve relevant images, and vice versa.
- Works well for image-text matching but may not capture fine-grained details.

**3. Multi-modal LLM at generation time:**

- Retrieve relevant images/documents as raw content (not just text).
- Pass them directly to a multi-modal LLM (Claude, GPT-4V) that can "see" the images alongside text.
- Most flexible but most expensive.

**4. Hybrid pipeline:**

- Maintain separate indexes for text and images.
- Route queries to the appropriate index (or both).
- Combine results before sending to a multi-modal LLM.

**Production consideration:** Multi-modal RAG is significantly more complex — chunking, embedding, and evaluation all become harder. Start with text-only RAG and add modalities incrementally.

---

### 29. Explain the difference between RAG and fine-tuning. When would you choose one over the other?

| Aspect           | RAG                                 | Fine-tuning                                |
| ---------------- | ----------------------------------- | ------------------------------------------ |
| Knowledge source | External documents at query time    | Baked into model weights                   |
| Update frequency | Instant (update the document store) | Requires retraining                        |
| Cost             | Per-query retrieval + generation    | Upfront training cost                      |
| Best for         | Factual Q&A over specific documents | Changing model behavior/style/format       |
| Hallucination    | Reduced (grounded in sources)       | Can still hallucinate                      |
| Data privacy     | Documents stay in your control      | Training data gets absorbed into weights   |
| Setup complexity | Vector DB + retrieval pipeline      | Training infrastructure + dataset curation |

**Choose RAG when:**

- Knowledge changes frequently (policies, product docs, news).
- You need citations and source attribution.
- You need to work with private/proprietary data without modifying the model.
- You want to avoid the cost and complexity of fine-tuning.

**Choose fine-tuning when:**

- You want to change the model's tone, format, or reasoning style.
- The model needs to learn domain-specific patterns (medical terminology, legal reasoning style).
- Latency is critical and you can't afford the retrieval step.
- The knowledge is stable and well-defined.

**Combining both:** Fine-tune a model for your domain's reasoning style and terminology, then use RAG for up-to-date factual grounding. This is the most powerful approach for production systems — the fine-tuned model is better at interpreting the retrieved context.

---

### 30. How do you handle document updates in a production RAG system?

When source documents change, the vector index becomes stale. Strategies for keeping it in sync:

**1. Full re-indexing:**

- Re-chunk and re-embed everything on a schedule (nightly, weekly).
- Simple but wasteful — most documents haven't changed.
- Viable for small corpora (under 100K documents).

**2. Incremental updates with change detection:**

- Track document hashes or modification timestamps.
- On each sync: detect new/modified/deleted documents.
- Only re-embed the changed chunks; delete vectors for removed documents.
- Requires a mapping between source documents and their vector IDs.

**3. Versioned documents:**

- Store a version field in chunk metadata.
- When a document updates, add new chunks with a new version and keep old ones.
- At query time, filter to the latest version.
- Periodically garbage-collect old versions.

**4. Event-driven pipeline:**

- Source systems (CMS, S3, databases) emit events when documents change.
- A pipeline listener picks up the event, re-chunks, re-embeds, and upserts to the vector DB.
- Near real-time freshness.

**Key challenges:**

- **Chunk ID stability** — if you re-chunk a modified document, the new chunks might not align 1:1 with the old ones. Safest to delete all old chunks for that document and insert the new set.
- **Embedding model changes** — if you upgrade your embedding model, you must re-embed the _entire_ corpus because old and new vectors aren't comparable.
- **Consistency** — during re-indexing, users might get results from a mix of old and new chunks. Use blue-green indexing (build a new index, then swap atomically) for zero-downtime updates.
