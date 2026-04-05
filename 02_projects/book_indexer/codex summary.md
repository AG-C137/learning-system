Сделай техническое саммари проекта book_indexer.

🎯 Цель

Кратко и точно описать текущую архитектуру и реализованный функционал, чтобы другой разработчик мог быстро понять систему.

📁 Ограничения
Пиши только по фактическому коду
Не выдумывай функциональность
Не делай предположений
Без воды
Объём: 200–400 строк
📌 Структура
1. Общая цель

Что система делает сейчас (фактически)

2. Pipeline

Опиши:

scan_directory
build_book
parsers (fb2 / epub / pdf)
raw_text
chunking
embeddings
storage (SQLite)
3. EPUB (подробно)
_extract_spine_text
фильтры:
href
длина
слова
ограничения:
TEXT_LIMIT
chunks limit
4. Модель данных
Book
таблица books
таблица book_chunks
5. Retrieval
как считается similarity
keyword boost
фильтры чанков
top-N
6. RAG (ask2)
pipeline
normalize_query
context сборка
prompt
7. Quality control (ВАЖНО)

Опиши:

threshold (max_score)
definition detection (looks_like_definition)
fallback логика
8. CLI
index
search
show
ask2
9. Ограничения

Только фактические:

PDF
отсутствие vector index
отсутствие grouping по книге
отсутствие entity matching
загрузка всех embeddings в память
и т.д.

Если что-то не видно в коде — пропусти.


1. Общая Цель

book_indexer сейчас индексирует книги из каталога в SQLite.
Система сканирует файловую директорию, пытается извлечь метаданные и текст, сохраняет книги и чанки, считает embeddings, даёт обычный поиск и RAG-поиск через CLI.
Поддержанный по коду парсинг есть для fb2, fb2.zip, epub, pdf.
Обычный поиск работает по name/title/author.
Семантический поиск работает по таблице book_chunks и embeddings.
ask2 строит ответ через локальную LLM с контекстом из найденных чанков либо уходит в fallback без контекста.
2. Pipeline

Входная точка CLI находится в main.py.
Команда index вызывает init_db(DB_PATH).
Затем вызывается scan_directory(path).
scan_directory рекурсивно обходит каталог через Path(path).rglob("*").
В индекс попадают только файлы, у которых detect_book_extension(file) входит в BOOK_EXTENSIONS.
BOOK_EXTENSIONS включает: .pdf, .fb2, .epub, .txt, .djvu, .doc, .docx, .fb2.zip.
После сканирования для каждого файла вызывается get_book_file_info(f, DB_PATH).
Затем вызывается build_book(f, existing_meta).
build_book создаёт объект Book(path).
В Book сразу заполняются path, name, extension.
В build_book читаются size и mtime файла.
Если есть старая запись, система сравнивает старые size/mtime с текущими.
При совпадении size/mtime книга считается unchanged, если выполнено одно из условий:
Есть и description, и raw_text.
Либо для расширения нет парсера.
Либо расширение равно .pdf.
Для unchanged возвращается (None, "unchanged").
Если запись уже была, в объект Book подставляются старые description, raw_text, user_notes.
Парсер берётся через get_parser(book.extension).
Если парсер существует, вызывается parser.parse(path).
Если ParseResult.status != "failed", в Book записываются title, author.
Если result.text есть, текст нормализуется через normalize_text.
Затем нормализованный текст кладётся в book.raw_text.
Затем book.raw_text режется на чанки через split_into_chunks.
Если текста нет, book.raw_text = None, book.chunks = [].
Если description ещё нет и result.text существует, вызывается generate_description(result.text).
Далее save_index_sqlite пишет книги и чанки в SQLite.
Для книг со статусом added или updated старые чанки удаляются.
Потом вставляются новые строки в book_chunks.
После этого для всех чанков без embedding вызывается get_embedding(text).
Embedding сохраняется в book_chunks.embedding как JSON-строка.
После сохранения вызывается mark_seen_bulk(paths, DB_PATH, current_run).
Затем вызывается cleanup_missing_books(DB_PATH, path, current_run).
3. Parsers

Базовый контракт описан в base.py.
ParseResult содержит title, author, text, status, error.
status может быть только "ok", "partial", "failed".
Реестр парсеров находится в registry.py.
В реестре есть:
.fb2 -> FB2Parser()
.fb2.zip -> FB2Parser()
.epub -> EPUBParser()
.pdf -> PDFParser()
Для .txt, .djvu, .doc, .docx парсеры в реестре отсутствуют.
Функция clean_book_text в base.py существует, но в текущем pipeline не используется.
4. EPUB Подробно

EPUB-парсер находится в epub_parser.py.

Константа TEXT_LIMIT = 50_000.

parse() открывает EPUB как zipfile.ZipFile.

Сначала читается META-INF/container.xml.

Из container.xml извлекается rootfile.

Из rootfile.attrib["full-path"] берётся путь к OPF.

Затем читается OPF-файл.

title читается из dc:title.

author читается из dc:creator.

Основной текст собирается через _extract_spine_text(...).

_extract_spine_text сначала строит manifest.

В manifest кладётся соответствие item_id -> href.

Затем берётся base_dir = dirname(opf_path).

Дальше парсер проходит по элементам spine/itemref.

Для каждого itemref берётся idref, по нему ищется href.

Если href отсутствует, элемент пропускается.

Есть фильтр по имени href.

Пропускаются элементы, если в href.lower() есть один из маркеров:

"toc"

"nav"

"contents"

"cover"

"titlepage"

"copyright"

"imprint"

Путь внутри архива строится через normpath(join(base_dir, href)).

Если такого файла в архиве нет, KeyError перехватывается, элемент пропускается.

HTML очищается через _strip_html.

_strip_html использует кастомный _HTMLTextExtractor, основанный на HTMLParser.

При тегах p, div, br, li в буфер добавляется перевод строки.

Текстовые узлы очищаются через " ".join(data.split()).

После HTML-очистки идёт фильтрация текста.

Если текста нет или len(text) < 200, кусок пропускается.

Потом считается words = text.split().

Если слов меньше 50, кусок пропускается.

Затем вычисляется lower_text = text.lower().

Если в тексте больше 20 переводов строки и одновременно встречается одно из слов "глава", "chapter", "contents", кусок пропускается.

Дальше применяется общий лимит по длине.

remaining = TEXT_LIMIT - total.

Если remaining <= 0, цикл прерывается.

В parts добавляется только text[:remaining].

total увеличивается на len(piece) + 1.

chunks увеличивается на 1.

Есть ограничение if chunks >= 15: break.

Есть дополнительная остановка if total >= TEXT_LIMIT and chunks >= 1: break.

Результат собирается как " ".join(parts).strip().

Если после всех фильтров текста нет, возвращается None.

5. FB2 Подробно

FB2-парсер находится в fb2_parser.py.
Константа TEXT_LIMIT = 50_000.
Поддерживаются как .fb2, так и .fb2.zip.
Для .fb2.zip файл открывается как ZIP-архив.
В архиве ищется первый файл с расширением .fb2.
XML загружается через ElementTree.
Namespace определяется по корневому тегу.
Название читается из book-title.
Автор собирается из first-name и last-name.
Текст берётся из всех body.
По каждому body вызывается body.itertext().
Каждый текстовый фрагмент очищается через " ".join(chunk.split()).
Пустые фрагменты пропускаются.
Дальше работает только лимит длины TEXT_LIMIT.
Фрагменты добавляются последовательно до исчерпания лимита.
Результат собирается как " ".join(parts).strip().
Если текста нет, возвращается None.
6. PDF Подробно

PDF-парсер находится в pdf_parser.py.
Используется pypdf.PdfReader.
Константа TEXT_LIMIT = 15000.
Парсер обрабатывает только первые 10 страниц: reader.pages[:10].
Для каждой страницы вызывается page.extract_text().
Если текста нет, страница пропускается.
Текст страницы дополнительно strip()-ится.
Если длина текста страницы меньше 50, страница пропускается.
Все страницы склеиваются через "\n".join(parts).strip().
Если общий текст длиннее лимита, он обрезается до TEXT_LIMIT.
Возвращается ParseResult(title=path.stem, author=None, text=full_text|None, status="ok"|"partial").
При исключении возвращается status="failed" и error=str(e).
7. Raw Text И Chunking

raw_text хранится как нормализованный полный текст книги.
Нормализация делается в normalize_text(text).
В ней все \n заменяются на пробел.
Затем все последовательности пробельных символов схлопываются через re.sub(r"\s+", " ", text).
Результат обрезается strip().
Чанкинг делается в split_into_chunks(text, chunk_size=800, overlap=150).
Текст режется по предложениям через re.split(r"(?<=[.!?])\s+", text).
Пустые предложения пропускаются.
Чанк растёт, пока суммарная длина не превысит chunk_size.
При переполнении текущий чанк добавляется в chunks.
Затем новый чанк начинаетcя с overlap на уровне предложений.
Реально overlap берётся как последние 2 предложения предыдущего чанка.
Параметр overlap=150 в коде есть, но в логике не используется напрямую.
В конце оставшийся чанк тоже добавляется.
Чанки сохраняются в Book.chunks.
В Book атрибут chunks заранее не объявлен в конструкторе, он появляется динамически в builder.
8. Описание Книги

Генерация описания находится в describer.py.
Используется локальный Ollama endpoint http://localhost:11434/api/generate.
Модель: "mistral".
Перед вызовом текст книги схлопывается в одну строку.
Если после очистки текста меньше 200 символов, описание не создаётся.
Для prompt используется только первые 5000 символов.
Prompt просит краткое описание книги в 3–5 предложений.
Из ответа ещё раз удаляются лишние пробелы.
Описание сохраняется в books.description.
9. Модель Данных

Класс Book находится в book.py.

Поля объекта:

path

name

extension

title

author

description

raw_text

user_notes

Таблица books создаётся в SQLite со столбцами:

path TEXT PRIMARY KEY

name TEXT

ext TEXT

title TEXT

author TEXT

description TEXT

raw_text TEXT

user_notes TEXT

source_dir TEXT

size INTEGER

mtime REAL

last_seen REAL

Таблица book_chunks создаётся со столбцами:

id INTEGER PRIMARY KEY AUTOINCREMENT

book_path TEXT

chunk_index INTEGER

text TEXT

embedding TEXT

embedding хранится как JSON-строка, а не как отдельный vector-тип.

В sqlite.py есть миграционный код через PRAGMA table_info(...).

При необходимости автоматически добавляются колонки:

last_seen

description

raw_text

user_notes

embedding

10. Storage / SQLite

init_db(db_path) создаёт таблицы и докидывает недостающие колонки.
get_book_file_info(path, db_path) возвращает старые size, mtime, description, raw_text, user_notes.
save_index_sqlite(books_with_status, db_path, source_dir, current_run) выполняет основную запись.
Пути db_path и source_dir нормализуются через Path(...).resolve().
Для каждой книги сначала проверяется наличие записи по path.
На основе этого считаются счётчики added и updated.
Запись в books выполняется через INSERT OR REPLACE.
Для книг со статусом added или updated старые чанки удаляются из book_chunks.
Затем вставляются новые чанки с их chunk_index.
После вставки выбираются все чанки, у которых embedding IS NULL.
Для каждого такого чанка вызывается get_embedding(text).
Embedding-сервис использует Ollama endpoint http://localhost:11434/api/embeddings.
Модель: "nomic-embed-text".
В embedding prompt передаётся только text[:1000].
Если embedding успешно получен, он сериализуется через json.dumps(...).
cleanup_missing_books(db_path, source_dir, current_run) удаляет книги, которые не были отмечены в текущем запуске.
Условие удаления: source_dir = ? AND (last_seen IS NULL OR last_seen < current_run).
mark_seen_bulk(paths, db_path, current_run) обновляет last_seen для уже существующих записей.
Код удаления чанков осиротевших книг отдельно не реализован.
В cleanup_missing_books удаляются только строки из books.
11. Обычный Поиск

SQL-поиск находится в search.py.
Для SQLite регистрируется функция LOWER, использующая casefold().
Это даёт Unicode-insensitive поиск по строкам.
Поиск идёт через LIKE по полям:
name
title
author
Запрос строится как %{text}%.
search() в CLI сортирует результаты по (title or "").lower().
На вывод берутся первые 20 записей.
show() показывает первый найденный результат и печатает:
title
author
description
path
12. Retrieval

Семантический retrieval реализован в _get_semantic_top(text) в main.py.
Перед embedding запрос нормализуется через normalize_query(query).
normalize_query удаляет префиксы:
"что такое"
"что это"
"кто такой"
"что значит"
Embedding запроса считается той же моделью "nomic-embed-text".
Из SQLite выбираются все строки:
SELECT book_path, text, embedding FROM book_chunks WHERE embedding IS NOT NULL
Все такие строки загружаются в память через fetchall().
На каждый чанк накладывается текстовый фильтр:
Если текста нет, чанк пропускается.
Если len(chunk_text) < 300, чанк пропускается.
Embedding чанка парсится из JSON.
Базовая метрика сходства: cosine_similarity(a, b).
cosine_similarity считается вручную в Python.
После cosine score применяется эвристический boost по "объясняющим" маркерам в тексте чанка.
Если есть "— это", добавляется 0.08.
Иначе если есть " это ", добавляется 0.05.
Если есть "является", добавляется 0.05.
Если есть "представляет собой", добавляется 0.05.
Затем применяется keyword boost.
Запрос для keyword boost берётся из исходного text.lower(), а не из normalize_query.
Стоп-слова: "что", "такое", "это", "как", "когда", "почему", "где".
Слова короче 5 символов игнорируются.
Для каждого слова берётся root = word[:8].
Если root есть в тексте чанка, добавляется 0.03.
Если полное word есть в тексте чанка, добавляется 0.05.
Общий keyword boost ограничен сверху 0.15.
Есть path-based title boost.
Если нормализованный запрос целиком входит в book_path.lower(), добавляется 0.2.
После этого результаты сортируются по score по убыванию.
Затем применяется фильтр definition-like chunks.
Используется внутренняя функция is_definition(chunk_text), основанная на DEFINITION_PATTERNS.
Если definition-like результатов хотя бы 3, остаются только они.
Затем идёт дедупликация по book_path.
На одну книгу остаётся только один лучший chunk.
На выходе возвращаются максимум 10 элементов.
Формат возврата: список кортежей (score, book_path, text).
13. RAG / ask2

Команда ask2 вызывает semantic_search_and_answer(text).
Сначала вызывается _get_semantic_top(text).
Если результатов нет, включается fallback без контекста.
Иначе кортежи переводятся в список словарей:
{"score": score, "book_path": path, "text": chunk_text}
Затем считается max_score = max(chunk["score"] for chunk in chunks).
Потом вызывается rerank_chunks(question, chunks).
rerank_chunks делает один LLM-вызов через _generate_with_llm(prompt).
Для rerank в prompt включаются до 500 символов каждого чанка.
Чанки нумеруются как [1], [2], ...
Prompt просит выбрать номера фрагментов, которые прямо помогают ответить на вопрос.
Ответ должен быть в формате списка, например [1, 3, 5].
Из ответа regex-ом вытаскиваются все числа.
Индексы переводятся в zero-based.
Дубликаты убираются.
Если rerank вернул индексы, берутся первые 3 выбранных чанка.
Иначе берутся первые 3 чанка из retrieval.
Контекст строится как "\n\n".join(chunk["text"] for chunk in context_chunks).
Финальный ответ генерируется через ask_llm(question, context).
ask_llm использует отдельный prompt для режима с контекстом.
Этот prompt требует:
отвечать только по контексту
отвечать кратко и по существу
использовать определение, если оно есть
не придумывать информацию
говорить, что ответа нет, если в контексте его нет
После ответа CLI печатает блок === ANSWER ===.
Затем печатает === SOURCES ===.
В sources выводятся только реально использованные context_chunks, а не весь top-10.
14. Quality Control

В main.py задан SCORE_THRESHOLD = 0.82.
В semantic_search_and_answer печатается [debug] max_score=....
После выбора context_chunks считается has_definition.
has_definition использует looks_like_definition(chunk["text"]).
looks_like_definition работает без LLM, только на regex.
Если текста нет, функция сразу возвращает False.
Проверяется только начало текста: text[:300].lower().
Паттерны привязаны к началу строки.
Используются шаблоны:
^[^\.]{0,80}\s—\sэто\s
^[^\.]{0,80}\sэто\s
^[^\.]{0,80}\sявляется\s
^[^\.]{0,80}\sпредставляет собой\s
В semantic_search_and_answer печатается [debug] has_definition=....
Fallback включается, если выполняется хотя бы одно условие:
not context_chunks
max_score < SCORE_THRESHOLD
not has_definition
В fallback-режиме контекст не смешивается с общим ответом.
В этом режиме печатается сообщение:
Нет надёжной информации в базе. Генерирую общий ответ...
Затем вызывается ask_llm(question) без контекста.
Для режима без контекста ask_llm использует отдельный prompt:
ответить кратко
если не уверен, так и сказать
15. CLI

CLI-команды определены в main().
При старте печатается cli started.
Если аргументов нет, выводится список команд.
Реально поддерживаются команды:
index
search
show
ask
ask2
index <path> запускает полный pipeline индексации.
search <query> делает SQL-поиск по книгам.
show <query> показывает первую найденную книгу.
ask <query> делает только семантический поиск и печатает top results.
ask2 <query> делает retrieval + rerank + answer generation + fallback.
16. Ограничения По Фактическому Коду

Векторного индекса нет.
ANN / FAISS / HNSW / sqlite-vector не используются.
Retrieval делает полный SELECT всех embeddings из book_chunks.
Similarity считается в Python, а не в базе.
Все embeddings-кандидаты загружаются в память целиком.
Фильтрации по книге, автору, серии, типу документа до retrieval нет.
Entity matching нет.
Нормализации морфологии нет.
Лемматизации нет.
Стемминга нет.
Специального ранжирования по названию книги нет, кроме substring-boost по book_path.
Retrieval не читает books.title, только book_path, text, embedding.
Definition-detection в retrieval и looks_like_definition в quality guard используют разные эвристики.
Для ask2 используется один rerank LLM-вызов и один final-answer LLM-вызов.
Для fallback используется только один общий LLM-вызов без контекста.
PDF-парсинг ограничен первыми 10 страницами.
PDF-текст обрезается до 15000 символов.
OCR нет.
Извлечение таблиц, изображений, layout-структуры нет.
Для .txt, .djvu, .doc, .docx файлы сканируются, но парсеров в registry нет.
Это значит, что такие файлы могут попасть в scan, но не будут реально распарсены.
cleanup_missing_books удаляет записи из books, но по этому коду не удаляет связанные строки из book_chunks.
В book_chunks нет внешнего ключа на books.
Embedding-сервис и LLM-сервис жёстко завязаны на локальный Ollama по localhost:11434.
Конфигурации моделей через настройки или env в коде нет.
pypdf используется в коде PDF-парсера, но зависимость в pyproject.toml по этому срезу кода не описана.
В split_into_chunks аргумент overlap=150 не участвует в формуле overlap.
Book не описан как dataclass и не имеет фиксированной схемы для chunks.
В CLI остаётся диагностический print(book_indexer.__file__) при импорте main.py.
Для SQLite-поиска по description поиска нет.
Для RAG нет кэширования результатов retrieval или rerank.
Нет пакетной отправки embeddings в модель.
Нет транзакционного разделения на отдельный этап “build” и отдельный этап “embed”; embedding считается внутри save_index_sqlite.
Нет проверки качества ответа LLM после генерации.
Нет цитирования ответов по предложениям или по span-ам.
Источники в ask2 показывают только путь и score, без excerpt-а.
