Сделай техническое саммари проекта **book_indexer**.

🎯 Цель: кратко и точно описать текущую архитектуру и реализованный функционал, чтобы другой разработчик мог быстро понять систему.

---

## 📁 Ограничения

* Пиши только по фактическому коду
* Не выдумывай функциональность
* Не делай предположений
* Без воды и общих фраз
* Объём: 200–400 строк максимум

---

## 📌 Структура саммари

### 1. Общая цель проекта

* что делает система сейчас (фактически)

### 2. Поток данных (pipeline)

Опиши шаги:

* сканирование
* парсинг (по форматам: fb2 / epub / pdf)
* извлечение текста
* построение метаданных
* сохранение

---

### 3. EPUB парсинг (ВАЖНО)

Отдельно подробно:

* где находится код
* как работает `_extract_spine_text`
* какие фильтры применяются:

  * по href
  * по длине текста
  * по словам
* как ограничивается объём (chunks / TEXT_LIMIT)

---

### 4. Структура данных книги

Опиши модель книги:

* какие поля есть
* что сохраняется в индекс

---

### 5. Хранилище

* где хранится индекс (JSON / SQLite)
* как происходит обновление (added / updated / unchanged)

---

### 6. CLI

* основные команды:

  * index
  * search
  * show
  * ask2

---

### 7. Ограничения текущей реализации

* чего нет (например: raw_text, embeddings, semantic search)

---

## 📎 Формат

* Markdown
* Чёткие заголовки
* Минимум текста, максимум конкретики
* Можно вставлять короткие фрагменты кода (по делу)

---

Если какая-то часть не очевидна — пропусти её, не додумывай.


Ответ:

# 1. Общая цель проекта

`book_indexer` индексирует локальную библиотеку книг, извлекает из файлов базовые метаданные и текст, сохраняет их в SQLite и даёт несколько режимов поиска через CLI:

- обычный поиск по `name / title / author`
- semantic search по embeddings чанков текста
- RAG-ответ на вопрос по найденным чанкам

Поддерживаемые парсеры по факту кода:

- `fb2`
- `fb2.zip`
- `epub`
- `pdf`

---

# 2. Поток данных (pipeline)

## 2.1 Сканирование

Файл: [filesystem.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/scan/filesystem.py)

`scan_directory(path)`:

- рекурсивно обходит каталог через `Path(path).rglob("*")`
- берёт только файлы
- определяет расширение через `detect_book_extension()`
- фильтрует по `BOOK_EXTENSIONS`

Поддерживаемые расширения на уровне сканера:

```python
BOOK_EXTENSIONS = {
    ".pdf", ".fb2", ".epub", ".txt", ".djvu", ".doc", ".docx", ".fb2.zip"
}
```

Но реальные парсеры есть только для:

- `.fb2`
- `.fb2.zip`
- `.epub`
- `.pdf`

## 2.2 Построение книги

Файл: [builder.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/builder.py)

`build_book(path, existing_meta=None)`:

1. читает `size` и `mtime`
2. создаёт `Book(path)`
3. если запись уже есть:
   - сравнивает `size` и `mtime`
   - считает книгу `unchanged`, если:
     - файл не менялся
     - и уже есть одновременно `description` и `raw_text`
     - или парсер отсутствует
     - или расширение `.pdf`
4. если книга уже была в БД:
   - подставляет `description`
   - подставляет `raw_text`
   - подставляет `user_notes`
5. выбирает парсер через `get_parser(extension)`
6. вызывает `parser.parse(path)`
7. если парсинг успешен:
   - заполняет `title`
   - заполняет `author`
   - сохраняет `result.text` в `book.raw_text`
   - режет `raw_text` на `book.chunks`
   - если `description` ещё нет, вызывает `generate_description(result.text)`
8. возвращает:
   - `(None, "unchanged")`
   - `(book, "added")`
   - `(book, "updated")`

## 2.3 Парсинг по форматам

Регистрация парсеров: [registry.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/registry.py)

```python
PARSERS = {
    ".fb2": FB2Parser(),
    ".fb2.zip": FB2Parser(),
    ".epub": EPUBParser(),
    ".pdf": PDFParser(),
}
```

### FB2

Файл: [fb2_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/fb2_parser.py)

- читает XML через `ElementTree`
- для `.fb2.zip` сначала открывает ZIP и ищет первый `.fb2`
- извлекает:
  - `book-title`
  - `author/first-name`
  - `author/last-name`
- текст получает из всех `body` через `itertext()`
- ограничивает текст `TEXT_LIMIT = 15_000`

### EPUB

Файл: [epub_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/epub_parser.py)

- открывает EPUB как ZIP
- читает `META-INF/container.xml`
- находит `rootfile full-path`
- читает OPF
- извлекает:
  - `dc:title`
  - `dc:creator`
- текст получает через `_extract_spine_text()`

### PDF

Файл: [pdf_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/pdf_parser.py)

Текущая реализация:

```python
return ParseResult(title=path.stem, text=None, status="partial")
```

То есть:

- текст PDF не извлекается
- автор не извлекается
- title берётся из имени файла

## 2.4 Извлечение текста

Структура результата парсинга: [base.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/base.py)

```python
@dataclass
class ParseResult:
    title: Optional[str]
    author: Optional[str]
    text: Optional[str]
    status: Literal["ok", "partial", "failed"]
    error: Optional[str]
```

Сейчас `result.text` используется как исходный текст для:

- `raw_text`
- chunking
- генерации `description`

## 2.5 Построение описания

Файл: [describer.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/ai/describer.py)

`generate_description(text)`:

- нормализует пробелы
- не работает для текста короче 200 символов
- обрезает вход до 5000 символов
- шлёт POST на `http://localhost:11434/api/generate`
- использует модель `mistral`
- возвращает `response` из JSON

## 2.6 Сохранение

Файл: [sqlite.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/sqlite.py)

Во время `index`:

1. `init_db(DB_PATH)`
2. `save_index_sqlite(books_with_status, DB_PATH, path, current_run)`
3. `mark_seen_bulk(paths, DB_PATH, current_run)`
4. `cleanup_missing_books(DB_PATH, path, current_run)`

---

# 3. EPUB парсинг

Файл: [epub_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/epub_parser.py)

## 3.1 Где находится код

Основные элементы:

- `_HTMLTextExtractor`
- `EPUBParser.parse(...)`
- `EPUBParser._extract_spine_text(...)`

## 3.2 Как работает `_HTMLTextExtractor`

`_HTMLTextExtractor` наследуется от `HTMLParser`.

Что делает:

- `handle_starttag()` вставляет `"\n"` для тегов:
  - `p`
  - `div`
  - `br`
  - `li`
- `handle_data()`:
  - схлопывает пробелы внутри текстового узла
  - добавляет очищенный фрагмент в `parts`
- `get_text()`:
  - делает `"".join(self.parts)`
  - возвращает `strip()`

То есть EPUB-текст сохраняет часть структуры по строкам.

## 3.3 Как работает `_extract_spine_text`

Сигнатура:

```python
def _extract_spine_text(self, archive, root, opf_path, package_ns) -> str | None:
```

Алгоритм:

1. строит `manifest` как `id -> href`
2. вычисляет `base_dir = dirname(opf_path)`
3. инициализирует:
   - `parts = []`
   - `total = 0`
   - `chunks = 0`
4. проходит по `spine/itemref`
5. для каждого элемента:
   - получает `idref`
   - находит `href` в `manifest`
   - фильтрует служебные `href`
   - читает HTML-файл из ZIP
   - превращает HTML в текст через `_strip_html()`
   - применяет текстовые фильтры
   - обрезает по оставшемуся лимиту
   - добавляет в `parts`
   - увеличивает `total` и `chunks`
   - прерывает цикл по лимитам
6. объединяет `parts` через пробел
7. возвращает строку или `None`

## 3.4 Фильтры по `href`

Файл пропускается, если `href.lower()` содержит:

- `"toc"`
- `"nav"`
- `"contents"`
- `"cover"`
- `"titlepage"`
- `"copyright"`
- `"imprint"`

Код:

```python
if any(
    marker in href.lower()
    for marker in (
        "toc", "nav", "contents", "cover",
        "titlepage", "copyright", "imprint",
    )
):
    continue
```

## 3.5 Фильтры по тексту

После `_strip_html()`:

```python
if not text or len(text) < 200:
    continue
```

Дальше:

```python
words = text.split()
if len(words) < 50:
    continue
```

И ещё один фильтр:

```python
lower_text = text.lower()
if lower_text.count("\n") > 20 and any(
    x in lower_text for x in ["глава", "chapter", "contents"]
):
    continue
```

Итого часть spine отбрасывается, если:

- текст пустой
- текст короче 200 символов
- слов меньше 50
- текст выглядит как оглавление / navigation по эвристике

## 3.6 Ограничение объёма

Константа:

```python
TEXT_LIMIT = 15_000
```

Счётчики:

- `chunks` — число принятых частей
- `total` — суммарная длина

После добавления части:

```python
piece = text[:remaining]
parts.append(piece)
total += len(piece) + 1
chunks += 1
```

Остановка:

```python
if chunks >= 5:
    break

if total >= TEXT_LIMIT and chunks >= 1:
    break
```

Фактически EPUB берёт только начало книги:

- максимум 5 содержательных частей spine
- максимум 15_000 символов

---

# 4. Структура данных книги

Файл: [book.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/book.py)

Класс `Book` содержит:

- `path`
- `name`
- `extension`
- `title`
- `author`
- `description`
- `raw_text`
- `user_notes`

`chunks` не объявлен в `Book.__init__`, но создаётся динамически в `build_book()`.

## Что сохраняется в индекс

Таблица `books` хранит:

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

Таблица `book_chunks` хранит:

- `id`
- `book_path`
- `chunk_index`
- `text`
- `embedding`

---

# 5. Хранилище

## 5.1 SQLite

Основное хранилище: SQLite, файл `index.db`.

Файл: [sqlite.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/sqlite.py)

### Таблица `books`

```sql
CREATE TABLE IF NOT EXISTS books (
    path TEXT PRIMARY KEY,
    name TEXT,
    ext TEXT,
    title TEXT,
    author TEXT,
    description TEXT,
    raw_text TEXT,
    user_notes TEXT,
    source_dir TEXT,
    size INTEGER,
    mtime REAL,
    last_seen REAL
)
```

### Таблица `book_chunks`

```sql
CREATE TABLE IF NOT EXISTS book_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_path TEXT,
    chunk_index INTEGER,
    text TEXT,
    embedding TEXT
)
```

## 5.2 Миграции

SQLite-слой делает безопасные миграции через `PRAGMA table_info(...)`.

Для `books` дозаполняются колонки:

- `last_seen`
- `description`
- `raw_text`
- `user_notes`

Для `book_chunks`:

- `embedding`

## 5.3 Обновление индекса

`build_book()` возвращает:

- `"added"`
- `"updated"`
- `"unchanged"`

### `unchanged`

Файл считается `unchanged`, если:

- размер совпадает
- `mtime` совпадает
- и:
  - есть и `description`, и `raw_text`
  - или парсер отсутствует
  - или это `.pdf`

### `added` / `updated`

Если книга не `unchanged`, она попадает в `save_index_sqlite(...)`.

## 5.4 Сохранение книг

`save_index_sqlite(books_with_status, ...)`:

- принимает список пар `(book, status)`
- делает `INSERT OR REPLACE` в `books`
- считает статистику `added / updated`

## 5.5 Сохранение чанков

Для книг со статусом `added` или `updated`:

1. удаляются старые чанки:

```sql
DELETE FROM book_chunks WHERE book_path = ?
```

2. вставляются новые чанки из `book.chunks`

Для `unchanged` чанки не пересоздаются.

## 5.6 Embeddings

В `sqlite.py` есть `get_embedding(text)`:

- вызывает `http://localhost:11434/api/embeddings`
- использует модель `nomic-embed-text`
- режет текст до 1000 символов
- возвращает вектор или `None`

После сохранения книг выполняется дозаполнение:

```sql
SELECT id, text FROM book_chunks WHERE embedding IS NULL
```

Для всех чанков без embedding:

- считается embedding
- сохраняется как JSON-строка в `book_chunks.embedding`

Существующие embeddings не пересчитываются.

## 5.7 JSON-хранилище

В проекте есть [index.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/index.py) с `save_index(...)`, который сохраняет книги в JSON.

По текущему CLI он не используется.

---

# 6. CLI

Файл: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py)

## 6.1 `index`

```bash
book-index index <path>
```

Что делает:

- инициализирует БД
- сканирует каталог
- строит книги через `build_book`
- сохраняет книги в SQLite
- обновляет `last_seen`
- удаляет пропавшие книги
- печатает статистику:

```text
+<added> added
~<updated> updated
-<removed> removed
=<unchanged> unchanged
```

## 6.2 `search`

```bash
book-index search <query>
```

Использует [search.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/search.py).

SQL:

```sql
SELECT path, title, author, description
FROM books
WHERE
    LOWER(name) LIKE LOWER(?)
    OR LOWER(title) LIKE LOWER(?)
    OR LOWER(author) LIKE LOWER(?)
```

Особенности:

- Unicode-insensitive `LOWER` через `casefold()`
- сортировка по `title.lower()`
- вывод максимум 20 результатов

## 6.3 `show`

```bash
book-index show <query>
```

- использует `search(..., display=False)`
- берёт первый результат
- печатает:
  - `title`
  - `author`
  - `description`
  - `path`

## 6.4 `ask2`

```bash
book-index ask2 "<вопрос>"
```

Текущая реализация использует простой RAG-поток.

### Retrieval

Helper `_get_semantic_top(text)`:

1. нормализует запрос через `normalize_query()`:
   - убирает префиксы:
     - `что такое`
     - `что это`
     - `кто такой`
     - `что значит`
2. считает embedding запроса
3. читает из БД:

```sql
SELECT book_path, text, embedding FROM book_chunks WHERE embedding IS NOT NULL
```

4. фильтрует чанки:
   - пропускает `chunk_text` короче 300 символов
5. для каждого чанка:
   - считает cosine similarity
   - добавляет небольшие эвристические бонусы за объяснительные конструкции:
     - `"— это"`
     - `" это "`
     - `"является"`
     - `"представляет собой"`
   - добавляет keyword boost:
     - с `STOPWORDS`
     - по `root = word[:8]`
     - бонус capped через `min(boost, 0.15)`
6. сортирует результаты по score
7. возвращает top-10 чанков

### Генерация ответа

`ask_llm(question, context)`:

- отправляет prompt в `http://localhost:11434/api/generate`
- использует модель `mistral`
- просит:
  - отвечать только по контексту
  - кратко
  - не выдумывать
  - если ответа нет, сказать об этом

`semantic_search_and_answer(text)`:

- берёт top chunks из `_get_semantic_top`
- объединяет их в `context`
- печатает:

```text
=== ANSWER ===
```

- затем выводит ответ модели

---

# 7. Ограничения текущей реализации

Только по фактическому коду.

- Нет реального извлечения текста из PDF: [pdf_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/pdf_parser.py) возвращает только `title=path.stem`.
- Нет парсеров для `.txt`, `.djvu`, `.doc`, `.docx`, хотя эти расширения сканируются.
- Нет полнотекстового SQL-поиска по `raw_text` или `book_chunks.text`; обычный `search` ищет только по `name`, `title`, `author`.
- Нет отдельного векторного индекса; semantic search перебирает все строки `book_chunks` из SQLite в Python.
- Нет ограничения по размеру выборки при semantic search на уровне SQL; все чанки с embedding загружаются целиком.
- Нет цитирования источников или ссылок на конкретные chunks в ответе `ask2`; печатается только итоговый ответ модели.
- `_get_semantic_top()` сейчас не группирует результаты по книге; в top-10 могут попасть несколько чанков из одной книги.
- `Book.chunks` не объявлен в модели `Book`, а добавляется динамически в `build_book()`.
- `cleanup_missing_books()` удаляет записи из `books`, но код не удаляет связанные строки из `book_chunks`.
- В CLI остаются отладочные выводы:
  - `print(book_indexer.__file__)`
  - `print("cli started")`
- Ошибки сетевых вызовов к Ollama в `describer`, embeddings и `ask_llm` тихо гасятся возвратом `None` / `""`; детальной диагностики нет.
- Нет отдельной схемы для связей chunk -> title/author; для semantic search в чанках хранится только `book_path`, `chunk_index`, `text`, `embedding`.
- Нет тестов, миграционного фреймворка и настройки конфигурации путей/моделей в просмотренном коде.