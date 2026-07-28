# Vector Search

Finding and retrieving similar items in large data sets by comparing their vector representation. Vector search looks for similarity based on meaning and context. The distance between two vectors can be used to indicate similarity. There are many different distance metrics. The task of a vector database is to identify and retrieve a list of vectors that are closest to the vector of a query, using **distance metrics and a search algorithm**.


## Distance Metrics

- The core problem is to judge the distance between two vectors. This is done using various distance metrics. This is a function that takes two vectors as input and produce a distance value between them.
- The distance can take many shapes, it can be the geometric distance between two points, it could be an angle between the vectors, it could be a count of vector component differences, etc.
- Depending on the machine learning models vectors can go ~100 or go into thousands of dimensions
- The more dimensions there are the more time it takes to compute the distance between two vectors. Some similarity measures are more compute heavy than others. Therefore, different distance metrics balances the speed and accuracy of calculating distance.
- Choose a distance metrics that matches the model you are using. 

### Cosine similarity

- Uses angle between to vectors to measure distance. The smaller the angle the more similar. Mostly used in NLP. It measures similarity between documents regardless of magnitude.
- It reports angle of data

### Dot product

- Multiple two or more vectors
- It reports both angle and magnitude

### Squared Euclidean (L2- Squared)

- Sum of squared vector

### Manhattan (L1 Norm or Taxicab Distance)

- Compares the distance between a pair of vectors
- This is faster compared to L2 which is more accurate

### Hamming

- It computes how many changes are needed to convert one vector into another

## Choosing a metric

The metric is mostly not a free choice — the embedding model picks it and
everything else follows.

1. **Read the model card.** Embeddings are trained with a contrastive objective
   that has a specific similarity function baked in, and the geometry of the
   space is only meaningful under that function. Ranking by something else
   measures what the training never optimized. For text embeddings the answer is
   cosine essentially every time.
2. **Check whether the vectors are normalized.** If they are, cosine / inner
   product / L2 are all strictly decreasing functions of the same dot product,
   so they give identical rankings and the question dissolves.
3. **If they are not, ask whether magnitude carries signal.** Magnitude that is
   noise (document length, term frequency artifacts) argues for cosine, which
   divides it out. Magnitude that means something you want to rank on argues for
   dot product — but note it will systematically favour long vectors, which is a
   real bias rather than a bug.
4. **Special vector types override all of the above.** Binary or quantized
   vectors use Hamming / Jaccard. Those are not alternatives to cosine; they are
   what you use once the vectors are no longer real-valued.
5. **Only if the model card is silent** does empirical selection make sense:
   build a small labelled set (query → the chunk that should come back) and
   compare recall@k and MRR across metrics. Never pick by benchmarking latency —
   the metrics differ by a few percent of query time and the index dominates.

## Search Algorithm 

- KNN (K Neariest Neighbour)
- ANN (Approximate Nearest Neighbour)

ANN algo is used by vector databases. In indexes the vectors using ANN algo and stores the nearest vectors close together which enables faster search.

## pgvector

Supports the following distance function

- L2 distance
- (negetive) inner product
- cosine distance
- L1 distance
- Hamming distance (binary vectors)
- Jaccard distance (binary vectors)

### Operators and index opclasses

Each metric is an operator, and each operator has one matching index opclass:

| Operator | Metric | Index opclass |
|---|---|---|
| `<->` | L2 | `vector_l2_ops` |
| `<=>` | cosine distance | `vector_cosine_ops` |
| `<#>` | negative inner product | `vector_ip_ops` |
| `<+>` | L1 | `vector_l1_ops` |

`<#>` is *negative* inner product and `<=>` is a *distance* rather than a
similarity because index scans can only sort ascending — "most similar" has to
sort first.

Search is an `ORDER BY ... LIMIT`, never a `WHERE` match. Two embeddings are
essentially never bit-identical, so equality always returns nothing.

To get similarity back for display: `1 - (embedding <=> query)`.

### Two ways this fails silently

**Operator/opclass mismatch.** Our index is `vector_cosine_ops`, so queries must
order by `<=>`. Use `<->` and Postgres ignores the index and sequentially scans
every chunk — right answers, linear time, no warning. Confirm with
`EXPLAIN ANALYZE`; you want `Index Scan using transcript_chunks_embedding_idx`,
not `Seq Scan` + `Sort`. A `LIMIT` is also required for the index to be used.

**Overfiltering.** HNSW gathers roughly `hnsw.ef_search` (default 40) candidates
by walking the graph, and a `WHERE` clause filters *after* that. Filtering on a
selective column — say one ticker out of twenty — can leave 2 rows when you asked
for 5, with no error. Fixes, in order of preference: raise `ef_search`;
denormalize the filter column onto `transcript_chunks` and index it; or force an
exact scan when the filter is narrow enough that brute force is faster anyway.

`SET hnsw.ef_search = 100;` is session-scoped and must be >= the `LIMIT`.

### Detail specific to this project

Cohere `embed-english-v3.0` returns L2-normalized vectors. For unit vectors,
cosine / inner product / L2 all give the *same ranking*, so the metric choice
isn't load-bearing here. Check with
`SELECT vector_norm(embedding) FROM transcript_chunks LIMIT 5;` (expect ~1.0).

Queries must be embedded with `input_type="search_query"` and stored chunks with
`"search_document"`. v3 models project the two into a shared space differently;
mixing them degrades retrieval with no visible error.
