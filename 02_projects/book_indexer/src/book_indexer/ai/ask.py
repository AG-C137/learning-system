from __future__ import annotations

from typing import Any

import requests

from book_indexer.core.search import search_chunks
from book_indexer.models import Chunk

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"


def ask(query: str, chunks: list[Chunk], top_k: int = 5) -> str:
    results = search_chunks(query, chunks, top_k=top_k)
    if not results:
        return "No relevant information found in the library."

    context = "\n\n".join(chunk.text for _, chunk in results)
    context = context[:4000]

    prompt = (
        "Answer using ONLY the context. If not found, say 'I don't know'.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{query}"
    )

    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False,
                  "options": {
                        "num_predict": 300},
            },            
            timeout=60,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except (requests.RequestException, ValueError) as e:
        return f"Ask error: {e}"

    result = data.get("response")
    if isinstance(result, str) and result.strip():
        return result.strip()

    return "No response returned by Ollama."
