from __future__ import annotations

from typing import Any

import requests

from book_indexer.models import Chunk

OLLAMA_EMBEDDINGS_URL = "http://localhost:11434/api/embeddings"


def embed_text(text: str, model: str = "nomic-embed-text") -> list[float]:
    MAX_LEN = 2000
    text = text[:MAX_LEN]

    try:
        response = requests.post(
            OLLAMA_EMBEDDINGS_URL,
            json={"model": model, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except (requests.RequestException, ValueError) as e:
        print("EMBED ERROR:", e)
        return []

    embedding = data.get("embedding")
    if not isinstance(embedding, list):
        return []

    result: list[float] = []
    for value in embedding:
        if isinstance(value, (int, float)):
            result.append(float(value))

    return result


def embed_chunks(chunks: list[Chunk]) -> list[Chunk]:
    for i, chunk in enumerate(chunks):
        if i % 10 == 0:
            print(f"Embedding chunk {i}/{len(chunks)}")

        embedding = embed_text(chunk.text)
        if embedding:
            chunk.embedding = embedding

    return chunks