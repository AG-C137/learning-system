# Book Indexer Architecture

## Flow
index → parse → chunk → embed → sqlite

## Query
ask2 → semantic_search_and_answer → semantic_rank → ask_llm

## Storage
- books
- book_chunks (embedding)

## Important
Do NOT create new pipelines. Use existing functions.