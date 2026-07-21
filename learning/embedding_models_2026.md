# Vector Embeddings in 2026: A Practical Report for Earnings Call RAG

## 1. Leading Embedding Models — Specs Comparison

| Model | Provider | Dims (default / supported) | Context Window | MTEB Score | Price / 1M tokens | License |
|---|---|---|---|---|---|---|
| **gemini-embedding-001** | Google | 3072 / 3072, 1536, 768, 256 | 2,048 tokens | 68.32 (MTEB #1) | ~$0.006 | Closed |
| **NV-Embed-v2** | NVIDIA | 4096 | 32K tokens | 72.31 (MTEB English) | Self-hosted | CC-BY-NC |
| **voyage-3-large** | Voyage AI | 2048 / 2048, 1024, 512, 256 | 32K tokens | 65.1 | $0.06 | Closed |
| **voyage-finance-2** | Voyage AI | 1024 | 32K tokens | 0.831 NDCG@10 (finance) | $0.12 | Closed |
| **embed-v4.0** | Cohere | 1536 / 1536, 1024, 512, 256 | 128K tokens | 65.2 | $0.12 | Closed |
| **text-embedding-3-large** | OpenAI | 3072 / up to 3072 | 8K tokens | 64.6 | $0.13 | Closed |
| **text-embedding-3-small** | OpenAI | 1536 | 8K tokens | ~62 | $0.02 | Closed |
| **BGE-M3** | BAAI | 1024 | 8K tokens | ~63 | Self-hosted | MIT |
| **Qwen3-Embedding-8B** | Alibaba/BAAI | 4096 | 32K tokens | ~67 | Self-hosted | Open |

Notes: MTEB scores vary by leaderboard snapshot and task set. NV-Embed-v2's 72.31 is on the English-only MTEB subset; gemini-embedding-001's 68.32 leads the multilingual leaderboard.

---

## 2. Dimension Trends in Production RAG (2026)

The industry has converged around a pragmatic range:

- **1024 dimensions** — the historical default (Cohere embed-v3, BGE-M3, voyage-finance-2). Fits comfortably in pgvector HNSW indexes; fast ANN search.
- **1536 dimensions** — now a common "quality upgrade" tier (OpenAI 3-small, Cohere embed-v4 default). Roughly 50% more storage and compute than 1024 but measurable retrieval gains on general benchmarks.
- **3072+ dimensions** — reserved for maximum-accuracy scenarios (OpenAI 3-large, Gemini, NV-Embed-v2). Storage and HNSW index costs scale significantly; a 3072-dim HNSW index fits ~42 entries per 8KB page vs ~68 for a 1024-dim index.

**Matryoshka / MRL** (all top-tier models now use this): embeddings are trained so that the leading N dimensions are meaningful on their own. This decouples the "training dimension" from the "serving dimension." You can store at 1024 and recover most of the 1536 quality, or store at 256 for a high-speed candidate pass.

**The practical production default in 2026** for general-purpose English RAG is 1536 dims (using OpenAI 3-small, Cohere embed-v4 truncated, or voyage-3-large at 1024/1536). Self-hosted stacks default to BGE-M3 at 1024.

---

## 3. Decision Framework for Earnings Call RAG

Ranked by relevance to earnings call transcripts in pgvector:

### A. Domain Fit (most important)
General MTEB rankings consistently **mispredict** finance retrieval performance. FinMTEB (Feb 2025, 64 finance-specific datasets including earnings call transcripts) found domain-specific models significantly outperform general leaders. **Voyage-finance-2** is the only purpose-built finance embedding model available commercially — it targets earnings calls, 10-Ks, tabular data, and ConvFinQA-style numerical reasoning, and beats OpenAI 3-large by 7% and Cohere Embed v3 by 12% on financial retrieval.

### B. Context Window
Earnings call transcripts are long — often 5,000–15,000 tokens. Models with 8K limits (OpenAI, BGE-M3) will truncate. Cohere embed-v4's 128K window is the clear leader, followed by voyage-finance-2 and voyage-3-large at 32K. This matters: if you're chunking aggressively, 8K is fine, but if you want paragraph-level or section-level chunks with trailing context, 32K+ is significant.

### C. pgvector-Specific Dimension Cost
- 1024 dims: ~4KB per vector — fits well in HNSW; recommended for large corpora (>500K chunks)
- 1536 dims: ~6.1KB per vector — still manageable; standard HNSW config works well
- 3072+ dims: pushes index pages hard; benefits from `halfvec` storage or quantization in pgvector 0.8+

For earnings transcripts (relatively small corpus — a few thousand to tens of thousands of chunks), 1536 is not a storage problem. 3072 is overkill unless doing cross-modal retrieval.

### D. Cost
At $0.12/1M, Cohere embed-v4 and voyage-finance-2 are equivalent. At tens of millions of tokens (full earnings histories), the cost is still under $10 total — not a primary driver.

### E. Multimodal (slides, tables, PDFs)
Cohere embed-v4.0 is the only model that embeds interleaved text + images in the same vector space — relevant if you later want to index slide decks or PDF screenshots of earnings presentations. Voyage-finance-2 is text-only.

---

## Recommendation

**Primary: `voyage-finance-2` at 1024 dimensions**
- Only purpose-built commercial model for financial retrieval, explicitly trained on earnings call transcripts
- 32K context window handles large transcript chunks
- 1024 dims is a natural fit for pgvector HNSW with minimal tuning
- Same cost as Cohere ($0.12/1M)
- 7–12% retrieval improvement over general models on financial tasks

**If staying on Cohere: `embed-v4.0` at 1024 dimensions**
- 128K context window is the standout advantage for long transcripts
- Matryoshka means 1024 is a first-class output, not a downgrade from 1536
- Future-proof for multimodal (slides, PDFs)
- Only upgrade to 1536 if A/B tests show measurable recall improvement on your actual query set

**Avoid for this use case**: OpenAI and Gemini — their 8K/2K context windows are a liability for transcript-length text, and their general-benchmark superiority does not translate to financial domain retrieval.

---

## Sources
- [Best Embedding Models for RAG in 2026 — InnovativeAIS](https://innovativeais.com/blog/best-embedding-models-for-rag-in-2026)
- [Embedding Model Leaderboard: MTEB Rankings March 2026 — Awesome Agents](https://awesomeagents.ai/leaderboards/embedding-model-leaderboard-mteb-march-2026/)
- [Cohere embed-v4.0: specs, MTEB score, and cost — PythonAlchemist](https://www.pythonalchemist.com/embeddings/cohere-embed-v4)
- [Cohere Embed v4.0: 128K Context Windows — RAGWalla](https://ragwalla.com/blog/cohere-embed-v4-0-128k-context-windows-transform-rag-at-scale)
- [voyage-3-large: new state-of-the-art general-purpose embedding model — Voyage AI](https://blog.voyageai.com/2025/01/07/voyage-3-large/)
- [Domain-Specific Embeddings: Finance Edition (voyage-finance-2) — Voyage AI](https://blog.voyageai.com/2024/06/03/domain-specific-embeddings-finance-edition-voyage-finance-2/)
- [FinMTEB: Finance Massive Text Embedding Benchmark — arXiv](https://arxiv.org/abs/2502.10990)
- [gemini-embedding-001: Dimensions, Pricing and Usage Guide 2026 — TokenMix](https://tokenmix.ai/blog/gemini-embedding-001-dimensions-pricing-guide-2026)
- [pgvector: Fewer dimensions are better — Supabase](https://supabase.com/blog/fewer-dimensions-are-better-pgvector)
- [Best Embedding Models 2026 — FutureAGI](https://futureagi.com/blog/best-embedding-models-2025/)
