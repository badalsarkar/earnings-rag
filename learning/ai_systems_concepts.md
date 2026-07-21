# AI Systems: High-Level Concepts

## 1. Architecture Fundamentals

**Model layer**
- **Model types**: LLMs (autoregressive transformers), embedding models, rerankers, multimodal models, diffusion models. Know which one solves which problem — don't default to "throw an LLM at it."
- **Inference vs. training**: Systems work almost always sit at inference time. Training/fine-tuning is a separate concern (data curation, RLHF, distillation) — most "AI system" work is orchestration around a frozen or lightly-tuned model.
- **Context window**: The hard budget every architecture decision revolves around — what goes in it, what gets evicted, what gets summarized.

**System patterns**
- **RAG (Retrieval-Augmented Generation)**: retriever (vector DB / BM25 / hybrid) + ranker + generator. The dominant pattern for grounding models in private/current data.
- **Agents**: LLM + tool use + a loop (plan → act → observe → repeat). Core primitives: tool/function calling, memory (short-term = context, long-term = external store), planning/reasoning strategy (ReAct, plan-and-execute), termination conditions.
- **Multi-agent systems**: orchestrator/worker patterns, debate, hierarchical delegation. Adds coordination and consistency problems on top of single-agent ones.
- **Pipelines vs. agentic control flow**: deterministic pipeline (fixed steps, predictable, easy to test) vs. agentic (model decides next step, flexible but harder to bound/verify). Most production systems are pipelines with a few agentic islands, not fully autonomous loops.

**Data architecture**
- **Vector stores**: embedding dimensionality, ANN indexes (HNSW, IVF), hybrid search (dense + sparse/BM25), metadata filtering.
- **Chunking strategy**: how you split source documents materially changes retrieval quality — semantic boundaries vs. fixed-size windows, overlap.
- **Freshness/consistency**: cache invalidation, embedding drift when the underlying model changes, reindexing cost.

**Orchestration & infra**
- **Statelessness of the model call**: every architecture problem is really "how do I manage state around a stateless function call" — session state, conversation history, tool results.
- **Latency/cost tradeoffs**: streaming, model routing (cheap model for easy cases, expensive for hard), caching (prompt caching, semantic caching of responses), batching.
- **Observability**: tracing (which prompt/retrieval/tool call produced which output), eval harnesses, logging of intermediate steps — not just final output, because failures are usually in the middle of a chain.
- **Idempotency & retries**: model calls are unreliable (rate limits, timeouts, nondeterminism) — systems need retry logic, idempotent writes.

## 2. Security Fundamentals

**Prompt injection** — the AI-native vulnerability class, distinct from classic OWASP:
- *Direct*: user directly tries to override system instructions.
- *Indirect*: malicious instructions embedded in retrieved content (a web page, a document, a tool result) that the model treats as trusted context. Anything an LLM *reads* is an attack surface, not just what a user *types*.
- Mitigations: privilege separation between instructions and data, output filtering, treating retrieved/tool content as untrusted, constrained tool permissions, human-in-the-loop for consequential actions.

**Tool/agent security**
- **Least privilege for tools**: an agent with file-write, shell exec, or payment APIs is a remote-code-execution surface if it can be manipulated via injection. Scope tool permissions tightly; never give an agent more capability than the task needs.
- **Confused deputy problem**: agent acts with the system's authority but takes instructions that may come from a less-trusted source (retrieved doc, third-party API response).
- **Sandboxing**: code execution tools, browser tools, shell tools need process/filesystem isolation.

**Data security**
- **Training data leakage / memorization**: models can regurgitate sensitive training data.
- **PII in prompts/logs**: what gets sent to a third-party model API, what gets logged, what gets stored in vector DBs (embeddings can sometimes be partially inverted).
- **Data exfiltration via output**: a compromised agent can smuggle secrets out through generated text, markdown image links, tool calls (e.g., "summarize this doc" where the doc contains a prompt injection that tells the model to leak conversation history via a crafted URL).

**Model-level risks**
- **Jailbreaking**: adversarial prompts that bypass safety training.
- **Supply chain**: provenance of third-party models/weights/fine-tunes, dependency integrity for model-serving stacks.
- **Adversarial inputs**: crafted inputs causing misclassification (more relevant to vision/classification systems).

**Classic security still applies, just with new entry points**
- Authn/authz around the API layer (who can call the model, what data can they retrieve).
- Input validation before it hits the model (SQL/command injection if the model's output is used to construct queries — e.g., text-to-SQL agents).
- Rate limiting / cost-based DoS (an attacker can burn your API budget, not just crash a service).
- Output validation before executing model-generated code, SQL, or shell commands — never `eval` or execute LLM output unchecked.

## 3. Cross-Cutting Fundamentals

- **Non-determinism**: same input ≠ same output. Testing, caching, and debugging strategies all have to account for this — you can't assert exact string equality, you need eval-based or property-based checks.
- **Evals**: the AI-native replacement for unit tests on "quality" — golden datasets, LLM-as-judge, human review loops, regression tracking across model/prompt versions.
- **Grounding & hallucination control**: citations back to source, confidence signaling, retrieval-then-generate rather than generate-then-cite, refusal when evidence is insufficient.
- **Guardrails**: input classifiers, output classifiers, structured output constraints (schema-constrained generation) to bound what a model can produce.
- **Human-in-the-loop**: where autonomy is dangerous (financial actions, irreversible writes, external comms) — approval gates.
- **Cost/latency as a first-class architectural constraint**: unlike traditional CRUD systems, every request has a real, variable dollar cost — architecture decisions (model choice, context size, retrieval depth) are cost decisions.
