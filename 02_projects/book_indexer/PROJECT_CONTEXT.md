# Project Context: book_indexer

Это локальный RAG по книгам.

Стек:

* Python
* SQLite
* Ollama (LLM + embeddings)

Основной pipeline:
index → parse → chunk → embed → store → search → ask2

ask2:
semantic_search_and_answer:

* semantic_rank
* keyword boost
* rerank_chunks
* ask_llm

Правила:

* не менять архитектуру без причины
* не дублировать функции
* сначала читать код, потом писать

Цель:
сделать локальную knowledge base
