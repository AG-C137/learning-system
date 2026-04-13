Проект: book_indexer → эволюция в library + RAG систему

Текущее состояние:

* Calibre используется как source of truth (metadata.db + файлы)
* есть loader → загружает Book (метаданные + путь)
* есть chunker → извлекает текст (epub/txt) и режет на Chunk
* есть embedder → Ollama (nomic-embed-text)
* есть semantic search → cosine similarity
* есть ask() → простой RAG через Ollama (llama3)

Архитектура:

* ai/embedder.py → embeddings
* core/search.py → поиск
* ai/ask.py → RAG
* модели: Book → Chapter (пока не используется) → Chunk

Что работает:

* загрузка книг из Calibre
* извлечение текста
* чанкинг
* генерация embeddings
* semantic search по смыслу
* генерация ответа через LLM

Проблемы/ограничения:

* поиск только по одной книге (books[0])
* embeddings не кэшируются
* нет Chapter-level структуры
* LLM иногда слишком строго отвечает ("I don't know")

Следующий шаг:

* объединить chunks всех книг
* сделать поиск по всей библиотеке
