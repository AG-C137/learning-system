# Learning System

Структура:

- 00_environment — среда, установки, инструменты
- 01_methodology — методология обучения
- 02_projects — проекты
- 03_experiments — эксперименты
- 04_notes — заметки

# book_indexer

Local AI system for building a searchable knowledge base from a Calibre library.

## Features

- Load books from Calibre (metadata.db)
- Extract text (EPUB, TXT)
- Chunking
- Embeddings via Ollama (nomic-embed-text)
- Semantic search
- Simple RAG (llama3)

## Requirements

- Python 3.12+
- Ollama running locally

## Usage (example)

```python
from book_indexer.core.calibre_loader import load_calibre_books
from book_indexer.core.chunker import chunk_book
from book_indexer.ai.embedder import embed_chunks
from book_indexer.ai.ask import ask

books = load_calibre_books(db_path="...", library_path="...")
chunks = chunk_book(books[0])
chunks = embed_chunks(chunks)

print(ask("your question", chunks))
