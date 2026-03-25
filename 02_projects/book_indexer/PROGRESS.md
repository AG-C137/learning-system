# Book Indexer — progress summary

Repo: learning-system  
Branch: feature/book_indexer  
Project: 02_projects/book_indexer  

## Current state

Working CLI tool:

book-index index <dir>
book-index search <text>

Editable install:

pip install -e .

## Project structure

book_indexer/

src/book_indexer/

cli/main.py  
core/book.py  
core/builder.py  

scan/filesystem.py  

parsers/registry.py  
parsers/fb2_parser.py  
parsers/pdf_parser.py  
parsers/txt_parser.py  

storage/sqlite.py  
storage/search.py  

index.db

## Implemented

✔ scan directory
✔ extension filter
✔ parser registry
✔ Book model
✔ builder
✔ sqlite storage
✔ init_db
✔ get_book_record
✔ size / mtime
✔ incremental skip unchanged
✔ CLI commands
✔ entry point book-index
✔ editable install
✔ multi directory index

## Database schema

books:

path TEXT PRIMARY KEY
name TEXT
ext TEXT
title TEXT
author TEXT
source_dir TEXT
size INTEGER
mtime REAL

## Current behavior

book-index index books

adds files

book-index index books again

skips unchanged files

## Next steps

- last_seen
- delete missing files
- multi source clean
- config file
- hash
- full text search
- embeddings

## Status

Stable.
Safe to continue.