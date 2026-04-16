from fastapi import FastAPI
from book_indexer.core.search import search

app = FastAPI()


@app.get("/search")
def search_api(q: str):
    results = search(q)

    return {
        "results": results[:5]  # ограничим
    }