# Book Indexer — Codex Context

## Purpose

This project is a local file indexer for books (pdf, fb2, txt, etc).

It is NOT a simple script.
It is designed as a foundation for a future:

- knowledge base
- semantic search
- AI / RAG system

---

## Architecture (IMPORTANT)

Pipeline:

scan → build → storage

Responsibilities:

- scan → finds files on disk
- build → creates Book objects and extracts metadata (parsers)
- storage → persists data (sqlite)

STRICT separation of concerns:

- builder MUST NOT access database directly (except lightweight checks)
- storage handles all persistence
- CLI only orchestrates

---

## Current Features

- directory scan
- extension filtering
- parser registry (fb2, pdf, txt)
- Book model
- sqlite storage
- CLI interface (book-index)
- editable install

---

## Incremental Indexing (CRITICAL)

The system already supports incremental indexing:

- files are identified by path
- metadata includes:
  - size
  - mtime

Behavior:

- if file unchanged → skip parsing
- if file changed → re-parse and update
- if file new → insert

DO NOT break this behavior.

---

## Database

Table: books

Fields:

- path (PRIMARY KEY)
- name
- ext
- title
- author
- source_dir
- size
- mtime

SQLite is the single source of truth.

---

## Coding Rules (VERY IMPORTANT)

DO:

- keep architecture clean
- make minimal, safe changes
- preserve backward compatibility
- prefer small functions

DO NOT:

- remove incremental logic
- reintroduce full reindex (DELETE + INSERT all)
- mix storage logic into builder
- duplicate logic between modules

---

## How to Work on This Project

When implementing features:

1. Understand current flow
2. Modify only necessary parts
3. Avoid breaking existing behavior
4. Prefer extension over rewrite

---

## Next Task (Current Focus)

Implement safe file removal from index:

- add `last_seen` field
- update `last_seen` during indexing
- delete records not seen in current scan

Requirements:

- MUST NOT break incremental skip logic
- MUST NOT delete valid records
- MUST work with multiple source_dir

---

## Preferred Strategy

Instead of full cleanup:

- mark records as seen during scan
- after scan:
  DELETE WHERE last_seen < current_run

---

## Notes

This project is evolving step-by-step.
Stability is more important than speed.

Avoid large refactors unless explicitly requested.