from __future__ import annotations

import math

from book_indexer.ai.embedder import embed_text
from book_indexer.models import Chunk


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for value_a, value_b in zip(a, b):
        dot_product += value_a * value_b
        norm_a += value_a * value_a
        norm_b += value_b * value_b

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))


def search_chunks(
    query: str, chunks: list[Chunk], top_k: int = 5
) -> list[tuple[float, Chunk]]:
    query_embedding = embed_text(query)
    if not query_embedding:
        return []

    scored_chunks: list[tuple[float, Chunk]] = []

    for chunk in chunks:
        if not chunk.embedding:
            continue

        score = cosine_similarity(query_embedding, chunk.embedding)
        if score > 0.2:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    limit = max(0, top_k)
    return scored_chunks[:limit]
