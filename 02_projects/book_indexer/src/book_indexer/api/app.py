from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from book_indexer.api.service import ask, search

app = FastAPI()

# ← ВОТ СЮДА добавляется CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str
    book: str | None = None
    author: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask_api(req: AskRequest):
    return ask(
        query=req.query,
        book=req.book,
        author=req.author,
        debug=False
    )


@app.get("/search")
def search_api(q: str):
    return {
        "results": search(q)[:10]
    }
