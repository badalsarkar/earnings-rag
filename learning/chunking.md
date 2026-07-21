# Chunking

## Why is it needed?

Chunking basically means splitting large text into smaller pieces. This is done to fit the content in the context window of LLM. It is very crucial for getting relevant generation from LLM. Chunking is also relevant for latency, improved response from LLM and efficiency.

### Chunking Strategies
#### Fixed chunking

- Segmenting text into equally sized pieces (character, tokens or word counts)
- Pros: simple
- Cons: Can loose semantic meaning, can cut off sentences, important information is scattered around the chunks
- Best for: Uniform document with consistent formatting 

#### Semantic chunking

- Splits documents in logical boundaries (sentence, paragraph, sections etc)
- Pros:
    - Preserves the flow of ideas
    - Keeps related concepts together improving retrieval accuracy
- Cons: Complex to implement, computational intensive
- Best for: Well-structured, narrative, or academic documents where continuity is crucial.

#### Recursive chunking

TODO

## References

1. https://community.databricks.com/t5/technical-blog/the-ultimate-guide-to-chunking-strategies-for-rag-applications/ba-p/113089

