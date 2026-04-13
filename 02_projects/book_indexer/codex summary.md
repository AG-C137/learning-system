# Техническое саммари `book_indexer`

## 1. Общая цель

`book_indexer` сейчас содержит две параллельные части:

1. legacy-пайплайн индексирования книг из файловой системы в SQLite;
2. новый набор модулей для Calibre-loading, chunking, embedding, semantic search и RAG-ответа.

По фактическому коду проект умеет:

- сканировать директорию с книгами;
- извлекать текст и метаданные для части форматов;
- сохранять индекс книг и чанков в SQLite;
- строить embeddings через локальный Ollama;
- выполнять семантический поиск по чанкам;
- генерировать ответ LLM по найденному контексту;
- отдельно загружать книги из `metadata.db` Calibre в dataclass-модель `Book`.

При этом в кодовой базе сейчас нет единой склейки между:

- `core/calibre_loader.py`;
- `core/chunker.py`;
- `ai/embedder.py`;
- `core/search.py`;
- `ai/ask.py`.

Эти модули существуют и рабочие по отдельности, но CLI по-прежнему в основном опирается на legacy-слой.

---

## 2. Текущая архитектура

### 2.1. Две разные модели книги

В проекте есть две разные сущности `Book`.

#### A. Новый dataclass-слой

Файл: `src/book_indexer/models.py`

Содержит dataclass-модели:

- `Book`
- `Chapter`
- `Chunk`

`Book`:

- `id: str`
- `title: str`
- `authors: list[str]`
- `path: str`
- `format: str`
- `language: Optional[str]`
- `tags: list[str]`
- `series: Optional[str]`
- `description: Optional[str]`
- `chapters: list[Chapter]`

`Chapter`:

- `id`
- `book_id`
- `title`
- `order`
- `text`
- `chunks`

`Chunk`:

- `id`
- `book_id`
- `chapter_id`
- `text`
- `embedding`
- `position`

У всех трёх dataclass есть `to_dict()` / `from_dict()`.

#### B. Legacy object-слой

Файл: `src/book_indexer/core/book.py`

Содержит отдельный класс `Book`, который используется старым pipeline.

Поля:

- `path`
- `name`
- `extension`
- `title`
- `author`
- `description`
- `raw_text`
- `user_notes`

Этот класс не совпадает по структуре с `book_indexer.models.Book`.

Это важная особенность проекта:

- новые RAG-модули работают через `book_indexer.models.Book` / `Chunk`;
- старый indexer/CLI работает через `core.book.Book`.

---

## 3. Новый pipeline: Calibre -> Chunk -> Embedding -> Search -> Ask

Ниже описан именно новый набор модулей.

### 3.1. Загрузка книг из Calibre

Файл: `src/book_indexer/core/calibre_loader.py`

Функция:

- `load_calibre_books(db_path: str, library_path: str) -> list[Book]`

Что делает:

- подключается к SQLite базе Calibre;
- читает таблицу `books`;
- для каждой книги поднимает связанные данные:
  - авторов;
  - теги;
  - серию;
  - доступные file entries из таблицы `data`;
- предпочитает `epub`, если у книги несколько форматов;
- собирает абсолютный путь к файлу книги;
- пропускает книгу, если файл не найден;
- возвращает список `book_indexer.models.Book`.

Вспомогательные функции:

- `_fetch_authors`
- `_fetch_tags`
- `_fetch_series`
- `_pick_file_entry`

Фактические особенности:

- `book.id` приводится к `str`;
- `chapters=[]`;
- `language` не заполняется;
- `description` не заполняется;
- при ошибке по строке есть `print("ERROR:", e)` и `raise`;
- при отсутствии файла есть `print("MISSING:", file_path)`.

### 3.2. Разбиение книги на чанки

Файл: `src/book_indexer/core/chunker.py`

Основная функция:

- `chunk_book(book: Book, chunk_size: int = 500, overlap: int = 50) -> list[Chunk]`

Поддерживаемые форматы по фактическому коду:

- `.txt`
- `.epub`

Если формат не поддержан:

- возвращается пустой список.

#### TXT extraction

- `_read_txt(path)` читает файл как UTF-8;
- при `OSError` или `UnicodeDecodeError` возвращает `""`.

#### EPUB extraction

Есть два пути:

1. `_read_epub_with_ebooklib(path)`
2. `_read_epub_from_zip(path)`

Порядок:

- сначала пробуется `ebooklib`;
- если не получилось или библиотека не установлена, используется zip/xml fallback.

#### EPUB через `ebooklib`

- импортируются `ITEM_DOCUMENT` и `epub`;
- читаются document items;
- HTML каждого item прогоняется через `_strip_html`;
- итог собирается через `"\n\n".join(parts).strip()`.

#### EPUB fallback через `zipfile`

- открывается архив EPUB;
- читается `META-INF/container.xml`;
- извлекается `rootfile`;
- читается OPF;
- из `manifest` строится `id -> href`;
- по `spine/itemref` читаются документы;
- HTML чистится через `_strip_html`;
- итог собирается через `"\n\n".join(parts).strip()`.

#### HTML cleanup

Используется:

- `_HTMLTextExtractor(HTMLParser)`
- `_strip_html(html_text)`

`_HTMLTextExtractor`:

- добавляет разделитель на тегах `p`, `div`, `br`, `li`, `h1..h6`;
- текстовые узлы очищает через `" ".join(data.split())`.

`_strip_html`:

- прогоняет HTML через parser;
- применяет regex cleanup;
- удаляет конструкции вида `\{...\}`;
- удаляет последовательности спецсимволов;
- удаляет токены `Cover@page`, `Converted Ebook`, `page`, `body` без учёта регистра;
- нормализует пробелы.

#### Формирование чанков

`chunk_book()`:

- получает текст через `_extract_text(book)`;
- если текста нет, возвращает `[]`;
- разбивает текст через `text.split()`;
- вызывает `_chunk_words(words, chunk_size, overlap)`;
- для каждого куска создаёт `Chunk`.

`Chunk` создаётся так:

- `id = f"{book.id}_{index}"`
- `book_id = book.id`
- `chapter_id = ""`
- `text = chunk_text`
- `embedding = None`
- `position = index`

#### Overlap logic

`_chunk_words()`:

- делает защиту `size = max(1, chunk_size)`;
- вычисляет шаг через:
  - `step = max(1, size - max(0, min(overlap, size - 1)))`
- режет список слов скользящим окном;
- сохраняет порядок чанков.

Фактические ограничения текущего chunker:

- `Chapter` в этом модуле не используется;
- разбиение идёт только по словам;
- абзацная структура отдельно не сохраняется;
- явной проверки `path.exists()` в текущем коде нет;
- ограничения по максимальной длине входного текста в `chunk_book()` сейчас нет.

### 3.3. Embeddings

Файл: `src/book_indexer/ai/embedder.py`

Функции:

- `embed_text(text: str, model: str = "nomic-embed-text") -> list[float]`
- `embed_chunks(chunks: list[Chunk]) -> list[Chunk]`

`embed_text()`:

- режет текст до `MAX_LEN = 2000`;
- делает `POST` на `http://localhost:11434/api/embeddings`;
- отправляет JSON:
  - `model`
  - `prompt`
- использует `requests`;
- timeout = `30`;
- при ошибке печатает `EMBED ERROR:` и возвращает `[]`;
- валидирует, что `embedding` из ответа является списком;
- приводит элементы embedding к `float`.

`embed_chunks()`:

- проходит по чанкам по порядку;
- каждые 10 чанков печатает прогресс;
- вызывает `embed_text(chunk.text)`;
- если embedding получен, записывает его в `chunk.embedding`;
- возвращает тот же список чанков.

Важно по архитектуре:

- `embedder.py` не импортирует `search`;
- circular import между embedding и search здесь нет.

### 3.4. Семантический поиск

Файл: `src/book_indexer/core/search.py`

Функции:

- `cosine_similarity(a: list[float], b: list[float]) -> float`
- `search_chunks(query: str, chunks: list[Chunk], top_k: int = 5) -> list[tuple[float, Chunk]]`

`cosine_similarity()`:

- реализована на чистом Python;
- не использует `numpy`;
- возвращает `0.0`, если:
  - один из векторов пустой;
  - длины не совпадают;
  - одна из норм равна нулю.

`search_chunks()`:

- строит embedding для query через `embed_text(query)`;
- пропускает чанки без `chunk.embedding`;
- считает cosine similarity;
- применяет порог:
  - в результат попадают только чанки со `score > 0.2`;
- сортирует по убыванию score;
- возвращает `top_k`;
- тип результата:
  - `list[tuple[float, Chunk]]`.

Фактическая зависимость:

- `search.py` импортирует `embed_text` из `ai.embedder`.

### 3.5. RAG / ask

Файл: `src/book_indexer/ai/ask.py`

Функция:

- `ask(query: str, chunks: list[Chunk], top_k: int = 5) -> str`

Поток работы:

1. вызывает `search_chunks(query, chunks, top_k=top_k)`;
2. если ничего не найдено, возвращает строку:
   - `"No relevant information found in the library."`
3. собирает context из `chunk.text` найденных чанков;
4. ограничивает context до `4000` символов;
5. вызывает Ollama generate endpoint;
6. возвращает текст ответа.

HTTP-вызов:

- URL: `http://localhost:11434/api/generate`
- библиотека: `requests`
- timeout = `60`
- JSON содержит:
  - `model: "llama3"`
  - `prompt`
  - `stream: False`
  - `options.num_predict = 300`

Prompt:

- требует отвечать только по context;
- если ответа нет, просит сказать `"I don't know"`.

Поведение при ошибке:

- если запрос или JSON-разбор падает:
  - возвращается строка вида `Ask error: ...`
- если в ответе нет текстового поля:
  - возвращается `"No response returned by Ollama."`

Архитектурно:

- `ask.py` импортирует `search_chunks`;
- обратной зависимости из `embedder.py` в `ask.py` нет.

---

## 4. Legacy pipeline: filesystem -> parser -> SQLite

Этот слой по фактическому коду всё ещё активен через CLI.

### 4.1. Сканирование файловой системы

Файл: `src/book_indexer/scan/filesystem.py`

Функция:

- `scan_directory(path: str)`

Что делает:

- рекурсивно проходит `Path(path).rglob("*")`;
- отбирает только файлы;
- фильтрует по `BOOK_EXTENSIONS`.

Поддержанные расширения для scanner:

- `.pdf`
- `.fb2`
- `.epub`
- `.txt`
- `.djvu`
- `.doc`
- `.docx`
- `.fb2.zip`

Важно:

- наличие расширения в scanner не означает наличие parser.

### 4.2. Parser registry

Файл: `src/book_indexer/parsers/registry.py`

Фактически зарегистрированы parser'ы только для:

- `.fb2`
- `.fb2.zip`
- `.epub`
- `.pdf`

Для:

- `.txt`
- `.djvu`
- `.doc`
- `.docx`

parser в registry нет.

### 4.3. Сборка книги

Файл: `src/book_indexer/core/builder.py`

Функции:

- `split_into_chunks(text, chunk_size=800, overlap=150)`
- `normalize_text(text)`
- `build_book(path, existing_meta=None)`

`build_book()`:

- создаёт legacy `core.book.Book`;
- сравнивает `size` и `mtime` с уже сохранёнными значениями;
- при unchanged может вернуть `(None, "unchanged")`;
- берёт parser по расширению;
- при удачном parse:
  - записывает `title`;
  - записывает `author`;
  - нормализует text;
  - сохраняет `raw_text`;
  - режет `raw_text` на string chunks;
  - при наличии текста генерирует description через `generate_description`.

Важно:

- тут чанки представлены как `list[str]`, а не как dataclass `Chunk`;
- этот слой не использует `models.py`.

### 4.4. Генерация описаний

Файл: `src/book_indexer/ai/describer.py`

Функция:

- `generate_description(text: str) -> str | None`

Что делает:

- берёт excerpt из текста;
- если текст слишком короткий, возвращает `None`;
- ограничивает excerpt до `5000` символов;
- вызывает Ollama `POST /api/generate`;
- модель:
  - `mistral`
- `stream = False`;
- просит кратко описать книгу;
- возвращает очищенный ответ или `None`.

### 4.5. SQLite storage

Файл: `src/book_indexer/storage/sqlite.py`

Что реализовано:

- создание таблицы `books`;
- создание таблицы `book_chunks`;
- миграционное добавление колонок при необходимости;
- сохранение книги;
- сохранение string chunks;
- расчёт embeddings для таблицы `book_chunks`;
- cleanup удалённых книг;
- обновление `last_seen`.

Таблица `books` содержит:

- `path`
- `name`
- `ext`
- `title`
- `author`
- `description`
- `raw_text`
- `user_notes`
- `source_dir`
- `size`
- `mtime`
- `last_seen`

Таблица `book_chunks` содержит:

- `id`
- `book_path`
- `chunk_index`
- `text`
- `embedding`

В `save_index_sqlite()`:

- для `added` и `updated` удаляются старые чанки книги;
- затем вставляются новые чанки;
- затем для строк `book_chunks`, у которых `embedding IS NULL`, вызывается `get_embedding(text)`;
- embedding сохраняется JSON-строкой.

В этом файле есть отдельный embedding-код через `urllib`, не через новый `ai/embedder.py`.

### 4.6. Текстовый поиск по SQLite

Файл: `src/book_indexer/storage/search.py`

Функции:

- `search_books(db_path: str, text: str)`
- `get_book_by_query(db_path: str, text: str)`

Поиск:

- идёт по таблице `books`;
- сравнивает `name`, `title`, `author`;
- использует кастомный SQLite function `LOWER`, основанный на `casefold()`.

Это не semantic search.

---

## 5. CLI

Файл: `src/book_indexer/cli/main.py`

CLI-команды по фактическому коду:

- `index`
- `search`
- `show`
- `ask`
- `ask2`

### `index`

- инициализирует SQLite DB;
- сканирует директорию;
- строит legacy `Book`;
- сохраняет книги и чанки в SQLite;
- обновляет `last_seen`;
- удаляет пропавшие книги;
- печатает статистику added/updated/removed/unchanged.

### `search`

- выполняет обычный SQLite-поиск по `name/title/author`.

### `show`

- берёт первый результат обычного поиска;
- печатает title, author, description, path.

### `ask`

- вызывает `semantic_search()`;
- использует legacy semantic search из `cli/main.py`;
- печатает top chunks и score.

### `ask2`

- вызывает `semantic_search_and_answer()`;
- использует legacy search по embeddings из SQLite;
- затем пытается ответить через LLM.

Важно:

- CLI сейчас не использует новый `core/search.py`;
- CLI сейчас не использует новый `ai/ask.py`;
- в `cli/main.py` есть свой embedding/search/RAG код.

Также в `cli/main.py` есть debug `print(book_indexer.__file__)`.

---

## 6. Что уже реализовано фактически

По коду уже есть:

- dataclass-модели `Book`, `Chapter`, `Chunk`;
- загрузка книг из Calibre SQLite;
- разбиение `.txt` и `.epub` книг на `Chunk`;
- EPUB extraction через `ebooklib` и zip/xml fallback;
- очистка HTML-текста EPUB;
- embedding чанков через Ollama `/api/embeddings`;
- cosine similarity без сторонних math-библиотек;
- semantic search по списку `Chunk` в памяти;
- RAG-функция `ask()` поверх `search_chunks()`;
- legacy индексирование файловой директории в SQLite;
- legacy semantic search по таблице `book_chunks`;
- legacy LLM answer flow в CLI.

---

## 7. Фактические ограничения и несостыковки

### 7.1. В проекте два pipeline

Сейчас одновременно существуют:

- новый in-memory pipeline на dataclass-моделях;
- старый SQLite/CLI pipeline на `core.book.Book`.

Они не сведены в один единый orchestration-слой.

### 7.2. Две разные модели книги

`core.book.Book` и `models.Book` решают похожую задачу, но несовместимы по полям и назначению.

### 7.3. Новый semantic search не подключён к CLI

`core/search.py` и `ai/ask.py` существуют, но CLI использует другой код из `cli/main.py`.

### 7.4. Chunker поддерживает только `.txt` и `.epub`

Новый `core/chunker.py` не работает с `.pdf`, `.fb2`, `.fb2.zip` и другими форматами.

### 7.5. `Chapter` пока не участвует в pipeline

Dataclass `Chapter` есть, но в новом chunking/search/ask коде не используется.

### 7.6. Глобального поиска по всем Calibre-книгам нет

Есть:

- загрузка списка книг из Calibre;
- chunking одной книги;
- embedding списка чанков;
- поиск по списку чанков.

Но функции уровня:

- загрузить все книги;
- начанкать все книги;
- объединить все чанки в один search corpus

в коде сейчас нет.

### 7.7. В коде есть дублирование embedding/RAG логики

Embedding и LLM-вызовы реализованы:

- в новых модулях `ai/embedder.py` / `ai/ask.py`;
- отдельно в `storage/sqlite.py`;
- отдельно в `cli/main.py`.

---

## 8. Фактическая схема зависимостей нового слоя

- `models.py`
  - базовые dataclass-модели

- `core/calibre_loader.py`
  - импортирует `models.Book`

- `core/chunker.py`
  - импортирует `models.Book`, `models.Chunk`

- `ai/embedder.py`
  - импортирует `models.Chunk`

- `core/search.py`
  - импортирует `ai.embedder.embed_text`
  - импортирует `models.Chunk`

- `ai/ask.py`
  - импортирует `core.search.search_chunks`
  - импортирует `models.Chunk`

По этим зависимостям circular import между:

- `embedder`
- `search`
- `ask`

сейчас нет.

---

## 9. Что можно считать текущим состоянием системы

Фактически проект находится в переходном состоянии.

С одной стороны:

- есть старый рабочий CLI-поток через SQLite.

С другой стороны:

- уже выделены более чистые модули для Calibre + Chunk + Embedding + Search + Ask.

Новый RAG-слой уже реализован как набор отдельных функций, но ещё не оформлен в единый end-to-end entrypoint, который:

- загружает все книги из Calibre;
- строит единый список чанков;
- эмбеддит его;
- выполняет search и ask по всей библиотеке.

Именно этого orchestration-слоя в фактическом коде сейчас нет.


Project: book_indexer

Current architecture:

* Models:

  * Book
  * Chapter (not actively used yet)
  * Chunk (text + embedding)

* Pipeline:
  Calibre → Book → Chunk → Embedding → Search → Ask (RAG)

---

Working components:

1. Calibre loader:

   * loads metadata from metadata.db
   * resolves file paths correctly

2. Chunker:

   * supports epub (ebooklib + zip fallback)
   * splits text into chunks with overlap

3. Embedder:

   * uses Ollama /api/embeddings
   * model: nomic-embed-text
   * assigns embedding to each Chunk

4. Search:

   * cosine similarity (pure Python)
   * filters score > 0.2
   * returns top_k (score, chunk)

5. Ask (RAG):

   * retrieves top chunks
   * builds context (<= 4000 chars)
   * calls Ollama /api/generate
   * model: llama3
   * stream=False

---

Important constraints:

* NO circular imports:

  * embedder must NOT import search
  * search CAN import embedder
  * ask CAN import search

---

Current limitation:

* Search is performed on a single book:
  chunks = chunk_book(books[0])

---

Next task:

Implement global search across ALL books.

Requirements:

1. Build a function:

   load_and_chunk_all_books(...) → list[Chunk]

2. Combine chunks from all books into one list

3. Optionally:

   * attach book_id or title to chunk for traceability

4. Reuse existing:

   * embed_chunks
   * search_chunks
   * ask

---

Goal:

User can ask:

"что такое биоэнергетика"

and get results from ANY book in the library.

---

Keep it simple:

* no database yet
* in-memory processing is fine
