1. **Архитектура**

- **Текущий рабочий контур**: CLI в [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:109) управляет всем pipeline: `index`, `search`, `show`, `ask`, `ask2`.
- **Сканирование**: [filesystem.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/scan/filesystem.py:18) рекурсивно обходит каталог и фильтрует файлы по расширениям.
- **Парсинг и подготовка книги**: [builder.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/builder.py:44) создаёт объект книги, вызывает parser из [registry.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/registry.py:7), нормализует текст, режет на чанки, при необходимости генерирует описание через Ollama.
- **Парсеры**: отдельные реализации для FB2, EPUB, PDF в [fb2_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/fb2_parser.py:9), [epub_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/epub_parser.py:33), [pdf_parser.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/pdf_parser.py:10).
- **Хранилище**: основной слой хранения сейчас в [sqlite.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/sqlite.py:138). Таблицы: `books` и `book_chunks`.
- **Поиск**: есть два разных слоя.
- Реально используемый для обычного `search`: [storage/search.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/search.py:11), поиск только по `name/title/author`.
- Отдельный семантический слой для RAG: функции `load_chunks`, `semantic_rank`, `rerank_chunks`, `ask_llm` прямо в [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:188).
- **AI-слой**: генерация описаний в [describer.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/ai/describer.py:6), альтернативные `embedder.py` / `ask.py` тоже есть, но в текущий CLI-контур почти не подключены.
- **Архитектурный риск**: в проекте одновременно живут две модели данных.
- `core.book.Book` используется рабочим pipeline: [book.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/book.py:11)
- `models.Book/Chapter/Chunk` используется альтернативным контуром: [models.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/models.py:69)
- **Вывод**: архитектура не единая. Есть активный SQLite+CLI pipeline и параллельный, частично недоведённый слой `models/core.search/ai.ask/storage.db`.

2. **Flow данных**

- **index**
- `book-index index <path>` в [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:109) вызывает `scan_directory()`.
- Для каждого файла вызывается `build_book()` в [builder.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/builder.py:44).
- Внутри `build_book()`:
- выбирается parser по расширению;
- извлекаются `title/author/text`;
- текст нормализуется;
- текст режется на строковые чанки `split_into_chunks()`;
- описание генерируется через `generate_description()`.
- **storage**
- `save_index_sqlite()` в [sqlite.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/sqlite.py:138) сохраняет книгу в `books`.
- Для `added/updated` книга сначала удаляет старые чанки, потом вставляет новые в `book_chunks`.
- Затем для всех чанков без embedding вызывается локальный Ollama `nomic-embed-text` и embedding пишется в `book_chunks.embedding`.
- По факту в текущей базе уже есть `12` книг и `2322` чанка.
- **search**
- Команда `search` использует только SQL `LIKE` по метаданным через [storage/search.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/search.py:11).
- Полнотекстовый поиск по `raw_text` не используется.
- **ask2**
- `ask2` парсит опции `--book/--author`, грузит все чанки из SQLite через `load_chunks()` в [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:188).
- Затем:
- optional filter по `title/author`;
- semantic ranking по cosine similarity;
- ручные бусты для definition/keyword/path;
- LLM-rerank через `rerank_chunks()`;
- выбор до 4 context chunks;
- либо прямой возврат definition chunk, либо генерация ответа через `ask_llm()`.

3. **Сильные стороны**

- Pipeline уже доведён до рабочего end-to-end цикла: сканирование, парсинг, чанкинг, embeddings, SQLite, поиск, `ask2`.
- Хорошо сделана инкрементальная индексация по `size/mtime` в [builder.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/builder.py:50): проект не перепарсивает всё без необходимости.
- Форматы FB2/EPUB/PDF реально поддержаны отдельными parser-классами, а не одним большим `if/else`.
- В SQLite есть разделение на `books` и `book_chunks`, то есть база уже готова к retrieval, а не только к каталогу.
- Для `ask2` есть полезные практические эвристики: нормализация запроса, keyword boost, special-case для определений, фильтр по книге/автору.
- Есть защита от сетевых/JSON ошибок при работе с Ollama и embeddings; приложение не падает на первом таймауте.
- `search_books()` делает Unicode-aware lowercase через `casefold`, что лучше стандартного `LOWER()` SQLite для кириллицы.

4. **Проблемы**

- **В проекте два конкурирующих доменных слоя**: `core.book.Book` и `models.Book/Chunk/Chapter` не совместимы по полям и используются разными модулями. Это не абстрактный долг, а реальный источник расхождения логики и дублирования кода: [book.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/book.py:11), [models.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/models.py:69), [storage/db.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/db.py:7), [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:188).
- **`ask2` теряет почти весь контекст книги**: в `semantic_rank()` после сортировки оставляется только один лучший chunk на книгу (`seen_books`), поэтому даже очень релевантная книга даёт максимум один chunk в ранжированном списке: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:292). Для RAG это серьёзное ухудшение recall.
- **Reranker фактически отключается в хорошем кейсе**: если LLM выбрал 1-2 лучших чанка, они игнорируются, потому что код применяет rerank только при `len(indices) >= 3`: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:478). Это контринтуитивная логика.
- **Fallback ломает grounded-answering**: если релевантных чанков нет, `ask2` переключается на общий LLM-ответ без контекста, то есть начинает отвечать не по базе, а “вообще”: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:469), [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:515).
- **Definition shortcut может отдавать сырой фрагмент вместо ответа**: при наличии “определения” код просто печатает chunk как есть: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:521). Это может вернуть оборванный кусок текста, а не ответ на вопрос.
- **`cleanup_missing_books()` удаляет книгу, но не её чанки**: из `books` запись удаляется, а `book_chunks` не чистится: [sqlite.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/storage/sqlite.py:237). Это прямой риск orphan-chunks и ложного retrieval после удаления файла.
- **Сканер принимает форматы, для которых нет parser-ов**: `.txt`, `.djvu`, `.doc`, `.docx` находятся в [filesystem.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/scan/filesystem.py:6), но в [registry.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/parsers/registry.py:7) поддержаны только `.fb2`, `.fb2.zip`, `.epub`, `.pdf`. Итог: в индекс попадут записи без текста и без чанков.
- **PDF помечается `unchanged` слишком рано**: условие в [builder.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/builder.py:53) считает любой PDF неизменённым только по `size/mtime`, независимо от полноты текста/описания. Если предыдущий parse был неполным, файл может так и не восстановиться.
- **API-слой поломан**: [api/app.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/api/app.py:2) импортирует `search` из `book_indexer.core.search`, но в [core/search.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/core/search.py:28) такой функции нет. Этот модуль в текущем виде не запустится.
- **Зависимости не соответствуют коду**: в [pyproject.toml](/home/ag137/Programs/learning-system/02_projects/book_indexer/pyproject.toml:5) указан только `pypdf`, но код импортирует ещё `requests`, `fastapi`, опционально `ebooklib`. Установка проекта “по инструкции” не воспроизводит runtime.
- **В одном файле смешаны CLI, retrieval, reranking, LLM и вывод**: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:1) слишком монолитен; это уже влияет на тестируемость и на риск регрессий, а не только на стиль.

5. **Качество RAG**

- **retrieval**
- База retrieval строится корректно: embeddings хранятся на уровне chunk в SQLite, а query embedding считается тем же `nomic-embed-text`.
- Но recall ограничен архитектурно: один chunk на книгу после `semantic_rank()` резко ухудшает поиск по длинным книгам.
- Есть эвристические бусты по keyword и pattern “X — это ...”, что может помогать на энциклопедических запросах.
- Нормализация запроса очень узкая: снимает только несколько русских префиксов.
- Поиск не использует BM25/full-text индекс; keyword boost идёт поверх уже урезанного embedding retrieval.

- **reranking**
- Reranking есть, но выполнен через тот же general LLM и только по первым 500 символам chunk: [main.py](/home/ag137/Programs/learning-system/02_projects/book_indexer/src/book_indexer/cli/main.py:396).
- Он нестабилен по формату: парсинг результата делается regex-ом по цифрам.
- Его влияние ограничено из-за порога `len(indices) >= 3`; хорошие rerank-результаты из 1-2 чанков просто не применяются.

- **answer generation**
- Положительная сторона: prompt явно требует отвечать по контексту и говорить “нет информации”, если данных нет.
- Но groundedness нарушается fallback-ветками на общий `ask_llm(question)` без контекста.
- Shortcut на definition chunk иногда повышает точность, но в реальности это уже не answer generation, а raw extractive return.
- Контекст ограничен `MAX_CONTEXT_CHUNKS = 4`; из-за ранней дедупликации по книге это часто 4 книги по одному фрагменту, а не 4 релевантных фрагмента одной темы.

6. **Технический долг**

- Две параллельные архитектуры данных и поиска: `core.book`/`storage.sqlite`/`cli.main` против `models`/`storage.db`/`core.search`/`ai.ask`.
- Дублирование low-level функций: embeddings и LLM-вызовы реализованы и в `main.py`, и в `ai/embedder.py`, `ai/ask.py`, `ai/describer.py`.
- Мёртвый или полуиспользуемый код: `core/chunker.py`, `storage/db.py`, `ai/ask.py`, `api/app.py` не встроены в основной контур.
- Нет согласованного dependency management под фактический runtime.
- Нет явных DB-индексов для retrieval-таблиц `book_chunks(book_path)` или поиска по `books`.
- Часть кода содержит debug-выводы в прод-потоке (`print(book_indexer.__file__)`, `[debug] raw_text_len`, `definition candidate`), что засоряет CLI и API.
- Нет тестового слоя для критичных сценариев: инкрементальная индексация, удаление книг, fallback Ollama, корректность `ask2`.

7. **Что делать дальше (приоритеты)**

- **P1. Зафиксировать один рабочий контур как основной**: либо оставить `cli.main + storage.sqlite`, либо переводить всё на `models/core.search/ai.ask`, но прекратить параллельное существование двух моделей данных.
- **P1. Исправить retrieval в `ask2`**: убрать дедупликацию “один chunk на книгу”, иначе RAG будет системно терять контекст.
- **P1. Исправить удаление данных**: при `cleanup_missing_books()` удалять и соответствующие строки из `book_chunks`.
- **P1. Убрать ungrounded fallback**: если в базе нет релевантных чанков, возвращать отсутствие данных, а не генерировать общий ответ.
- **P1. Привести `pyproject.toml` к реальному runtime**: добавить фактически используемые зависимости или удалить неиспользуемые модули.
- **P2. Разрезать `ask2` на отдельные функции/модули**: загрузка чанков, ranking, reranking, context selection, answer generation.
- **P2. Согласовать список поддерживаемых форматов**: либо добавить parser-ы для `.txt/.djvu/.doc/.docx`, либо убрать их из сканера.
- **P2. Починить API-слой**: `api/app.py` сейчас не соответствует реальному модулю поиска.
- **P2. Убрать дубли HTTP-клиентов к Ollama**: оставить одну точку вызова embeddings и одну точку вызова generation.
- **P3. Добавить тесты на критический pipeline**: `index -> sqlite -> ask2`, reindex unchanged, delete book, no-embedding/no-ollama paths.

Если хотите, следующим сообщением могу сделать вторую версию этого же аудита в формате “короткий executive summary + таблица рисков по severity”.