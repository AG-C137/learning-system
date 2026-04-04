📚 Проект: book_indexer — текущее состояние
🎯 Цель

Локальный индексатор библиотеки:

сканирует каталог книг
извлекает метаданные
хранит в SQLite
поддерживает поиск
готовится к AI-слою (описания / RAG)
🏗️ Архитектура
src/book_indexer/
├── cli/          → CLI (index, search)
├── scan/         → поиск файлов
├── core/         → Book + builder (added/updated/unchanged)
├── parsers/      → fb2 / fb2.zip / epub / pdf
├── storage/      → SQLite + search
⚙️ Что реализовано
1. Сканирование
рекурсивный обход каталога
поддержка:
.fb2, .fb2.zip, .epub, .pdf, .txt, и др.
2. Инкрементальная индексация
ключ: path
сравнение: size + mtime
статусы:
added
updated
unchanged
cleanup через last_seen
3. Парсинг (ключевой этап — уже работает)
FB2
XML parsing
исправлен namespace
FB2.ZIP
корректно определяется как отдельный тип
парсится через FB2 parser
EPUB
реализован через:
META-INF/container.xml
извлечение OPF
чтение:
dc:title
dc:creator
полностью рабочий (проверен вручную)
PDF
пока заглушка (title = filename)
4. Storage (SQLite)

Таблица books:

path (PK)
name
ext
title
author
size
mtime
source_dir
last_seen
5. Поиск
простой LIKE по:
title
author
name
работает
6. CLI (улучшен)

Команды:

book-index index <path>
book-index search <text>

Вывод поиска:

1. Название — Автор
   путь/к/файлу
🧠 Важные инженерные решения
введён ParseResult

единый интерфейс парсеров:

parse(path) -> ParseResult
builder:
не ломается при ошибке парсинга
создаёт запись даже при failed
⚠️ Ограничения
нет:
полнотекстового поиска
описаний книг
embeddings
FTS
EPUB/FB2 → только metadata, без текста
нет parse_status в БД (только в runtime)
📍 Текущая точка

Проект = рабочее ядро индексатора

Готов к следующему уровню:

👉 добавление AI-слоя

🚀 Следующий этап
🎯 Добавить описание книги (AI)

Что нужно сделать:

Расширить модель:
description (summary)

Добавить pipeline:

parser → text extract → LLM → summary
Реализовать:
извлечение текста (хотя бы частично)
генерацию описания
сохранение в БД
💡 Цель следующего чата

Сделать:

Книга → краткое описание (3–5 строк)

и заложить основу под:

RAG
локальную базу знаний

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


1. Общая цель проекта
book_indexer индексирует локальную директорию с книгами, извлекает базовые метаданные и текст из поддерживаемых форматов, генерирует краткое описание книги и сохраняет индекс в SQLite для дальнейшего поиска через CLI.

Фактически сейчас система умеет:

рекурсивно сканировать каталог на книги
определять формат по расширению
парсить .fb2, .fb2.zip, .epub, .pdf
извлекать title, author, ограниченный текстовый фрагмент
генерировать description через локальный HTTP API Ollama
сохранять/обновлять записи в SQLite
искать книги по name, title, author
показывать краткую карточку книги по запросу
Ключевые модули:

CLI: main.py
Сканирование: filesystem.py
Построение объекта книги: builder.py
Модель книги: book.py
Парсеры: registry.py
Хранилище SQLite: sqlite.py
Поиск: search.py
Генерация описания: describer.py
2. Поток данных (pipeline)
2.1 Сканирование
Источник: filesystem.py

scan_directory(path):

создаёт Path(path)
рекурсивно проходит base.rglob("*")
отбирает только файлы
определяет расширение через detect_book_extension()
включает файл, если расширение входит в BOOK_EXTENSIONS
Поддерживаемые расширения на этапе сканирования:

BOOK_EXTENSIONS = {
    ".pdf",
    ".fb2",
    ".epub",
    ".txt",
    ".djvu",
    ".doc",
    ".docx",
    ".fb2.zip"
}
Фактически парсеры зарегистрированы только для:

.fb2
.fb2.zip
.epub
.pdf
Файлы .txt, .djvu, .doc, .docx сканируются, но парсера для них в registry.py нет.

2.2 Построение книги
Источник: builder.py

build_book(path, existing_meta=None):

читает size и mtime файла через path.stat()
создаёт Book(path)
если запись уже есть в БД:
сравнивает старые size и mtime
если файл не изменился и:
уже есть description, или
парсер для расширения отсутствует, или
расширение .pdf
возвращает (None, "unchanged")
если запись уже была, переносит в объект:
description
user_notes
берёт парсер через get_parser(book.extension)
вызывает parser.parse(path)
если парсинг успешен:
записывает title
записывает author
если description ещё нет и есть result.text, вызывает generate_description(result.text)
если записи раньше не было, возвращает "added", иначе "updated"
2.3 Парсинг по форматам
Источник регистрации: registry.py

PARSERS = {
    ".fb2": FB2Parser(),
    ".fb2.zip": FB2Parser(),
    ".epub": EPUBParser(),
    ".pdf": PDFParser(),
}
FB2
Источник: fb2_parser.py

поддерживает обычный .fb2 и архивированный .fb2.zip
читает XML через ElementTree
извлекает:
book-title
author/first-name
author/last-name
текст собирает из всех body через itertext()
ограничивает объём до TEXT_LIMIT = 15_000
затем пропускает через clean_book_text()
EPUB
Источник: epub_parser.py

открывает EPUB как ZIP
читает META-INF/container.xml
находит rootfile full-path
загружает OPF
извлекает:
dc:title
dc:creator
текст получает из _extract_spine_text()
PDF
Источник: pdf_parser.py

Текущая реализация минимальная:

return ParseResult(title=path.stem, text=None, status="partial")
Фактически:

PDF-текст не извлекается
автор не извлекается
заголовок берётся из имени файла
2.4 Извлечение текста
Общая структура результата парсинга описана в base.py:

@dataclass
class ParseResult:
    title: Optional[str] = None
    author: Optional[str] = None
    text: Optional[str] = None
    status: Literal["ok", "partial", "failed"] = "ok"
    error: Optional[str] = None
Нормализация текста выполняется функцией clean_book_text(text):

схлопывает пробелы через " ".join(text.split())
разбивает по ". "
выбрасывает части короче 40 символов
собирает обратно строку
Эта очистка применяется в:

FB2
EPUB
2.5 Построение метаданных
Базовые метаданные книги формируются из двух источников:

файловая система:
path
name
extension
size
mtime
парсер:
title
author
text
Далее по text может генерироваться description.

Источник: describer.py

generate_description(text):

нормализует текст
прекращает работу, если текст пустой или короче 200 символов
обрезает до 5000 символов
отправляет POST на http://localhost:11434/api/generate
использует модель "mistral"
ожидает JSON с полем response
возвращает очищенный текст ответа
Промпт просит:

краткое описание книги в 3–5 предложениях
без выдумывания фактов
только по предоставленному тексту
2.6 Сохранение
CLI вызывает:

init_db(DB_PATH)
save_index_sqlite(books, DB_PATH, path, current_run)
mark_seen_bulk(paths, DB_PATH, current_run)
cleanup_missing_books(DB_PATH, path, current_run)
Это происходит в index(path) из main.py.

3. EPUB парсинг
Источник: epub_parser.py

3.1 Где находится код
Основной EPUB-код:

класс EPUBParser
вспомогательный HTML-экстрактор _HTMLTextExtractor
ключевая функция _extract_spine_text(...)
3.2 Как работает _extract_spine_text
Сигнатура:

def _extract_spine_text(
    self,
    archive: zipfile.ZipFile,
    root: ET.Element,
    opf_path: str,
    package_ns: str,
) -> str | None:
Алгоритм:

строит manifest:
читает все manifest/item
сохраняет id -> href
вычисляет base_dir = dirname(opf_path)
инициализирует накопление:
parts: list[str] = []
total = 0
chunks = 0
проходит spine/itemref
для каждого itemref:
берёт idref
ищет href в manifest
пропускает, если href отсутствует
фильтрует служебные файлы по href.lower()
собирает member_path = normpath(join(base_dir, href))
читает HTML из ZIP
преобразует HTML в текст через _strip_html()
применяет текстовые фильтры
добавляет фрагмент в parts
увеличивает total и chunks
прерывает цикл по лимитам
объединяет parts через пробел
пропускает итог через clean_book_text()
возвращает строку или None
3.3 HTML -> текст
Вспомогательный класс _HTMLTextExtractor(HTMLParser):

в handle_data() схлопывает пробелы
добавляет непустые текстовые куски в self.parts
get_text() возвращает " ".join(self.parts)
Функция _strip_html(html_data):

декодирует HTML как UTF-8 с errors="ignore"
прогоняет через _HTMLTextExtractor
возвращает плоский текст без HTML-тегов
3.4 Фильтры по href
В _extract_spine_text() EPUB-часть пропускается, если href.lower() содержит один из маркеров:

"toc"
"nav"
"contents"
"cover"
"titlepage"
"copyright"
"imprint"
Фактический код:

if any(
    marker in href.lower()
    for marker in (
        "toc",
        "nav",
        "contents",
        "cover",
        "titlepage",
        "copyright",
        "imprint",
    )
):
    continue
Это отсекает оглавление, navigation-файлы, обложку и часть служебных страниц до чтения HTML.

3.5 Фильтры по тексту
После _strip_html() применяются проверки:

if not text or len(text) < 200:
    continue

words = text.split()
if len(words) < 50:
    continue
То есть секция отбрасывается, если:

текст пустой
длина текста меньше 200 символов
меньше 50 слов
Дополнительный эвристический фильтр:

lower_text = text.lower()
if lower_text.count("\n") > 20 and any(
    x in lower_text for x in ["глава", "chapter", "contents"]
):
    continue
По факту _HTMLTextExtractor.get_text() склеивает текст пробелами, поэтому после _strip_html() символов перевода строки обычно не остаётся. Этот фильтр есть в коде, но его срабатывание зависит от того, сохранились ли \n во входном тексте после обработки.

3.6 Ограничение объёма
В EPUB используется общий лимит:

TEXT_LIMIT = 15_000
На уровне _extract_spine_text() объём ограничивается двумя счётчиками:

chunks — число принятых содержательных частей
total — суммарная длина уже добавленного текста
После каждой принятой части:

piece = text[:remaining]
parts.append(piece)
total += len(piece) + 1
chunks += 1
Остановка:

если remaining <= 0
если chunks >= 5
если total >= TEXT_LIMIT and chunks >= 1
Фактически функция берёт только начало книги:

максимум 5 содержательных частей spine
максимум 15_000 символов суммарно
3.7 Текущее поведение, видимое в коде
В текущем _extract_spine_text() остались отладочные print(...):

print("CHUNKS:", chunks)
print("TOTAL:", total)
print(piece[:200])
print("----")
Это означает, что при EPUB-парсинге код сейчас пишет диагностический вывод в stdout.

4. Структура данных книги
Источник: book.py

Класс Book хранит:

path
name
extension
title
author
description
user_notes
Инициализация:

class Book:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.extension = detect_book_extension(path)

        self.title = None
        self.author = None
        self.description = None
        self.user_notes = None
Особенность detect_book_extension(path):

если имя заканчивается на .fb2.zip, возвращает именно .fb2.zip
иначе возвращает обычный path.suffix.lower()
Что сохраняется в индекс
Фактически в SQLite сохраняются поля:

path
name
ext
title
author
description
user_notes
source_dir
size
mtime
last_seen
Схема таблицы находится в sqlite.py.

5. Хранилище
5.1 Основное хранилище
Основное используемое хранилище: SQLite.

Источник: sqlite.py

CLI использует файл:

DB_PATH = "index.db"
Таблица books:

CREATE TABLE IF NOT EXISTS books (
    path TEXT PRIMARY KEY,
    name TEXT,
    ext TEXT,
    title TEXT,
    author TEXT,
    description TEXT,
    user_notes TEXT,
    source_dir TEXT,
    size INTEGER,
    mtime REAL,
    last_seen REAL
)
5.2 Обновление индекса
added
Книга получает статус "added", если записи в БД раньше не было.

Это определяется в build_book(...) по existing_meta is None.

updated
Книга получает статус "updated", если запись уже была, но не попала в ветку "unchanged".

unchanged
Книга считается "unchanged", если одновременно:

размер файла не изменился
mtime не изменился
и дополнительно выполняется хотя бы одно:
в БД уже есть description
парсер для расширения отсутствует
расширение книги .pdf
Фактическая проверка в builder.py:

if (
    old_size == size
    and old_mtime == mtime
    and (
        existing_meta["description"]
        or get_parser(book.extension) is None
        or book.extension == ".pdf"
    )
):
    return None, "unchanged"
5.3 Сохранение и удаление
save_index_sqlite(...):

для каждой книги делает SELECT 1 FROM books WHERE path = ?
увеличивает счётчик added или updated
выполняет INSERT OR REPLACE
mark_seen_bulk(...):

массово обновляет last_seen для путей, обнаруженных в текущем сканировании
cleanup_missing_books(...):

удаляет записи из той же source_dir, которых не было в текущем проходе
условие удаления:
last_seen IS NULL OR last_seen < current_run
5.4 JSON-хранилище
В проекте есть index.py, который умеет сохранять список книг в JSON через save_index(books, path).

По фактическому коду CLI этот JSON-вариант сейчас не используется.

6. CLI
Источник: main.py

6.1 index
Команда:

book_indexer index <path>
Фактически делает:

инициализацию БД
сканирование директории
построение Book для каждого файла
сохранение/обновление записей в SQLite
обновление last_seen
удаление пропавших файлов из индекса
печать статистики
Формат вывода:

+<added> added
~<updated> updated
-<removed> removed
=<unchanged> unchanged
6.2 search
Команда:

book_indexer search <text>
Фактически:

открывает SQLite
ищет по полям:
name
title
author
использует LIKE '%query%'
переопределяет SQLite-функцию LOWER на Python casefold() для Unicode-insensitive поиска
сортирует результат по title.lower()
ограничивает вывод первыми 20 результатами
SQL из search.py:

SELECT path, title, author, description
FROM books
WHERE
    LOWER(name) LIKE LOWER(?)
    OR LOWER(title) LIKE LOWER(?)
    OR LOWER(author) LIKE LOWER(?)
6.3 show
Команда:

book_indexer show <text>
Фактически:

вызывает search(text, display=False)
берёт первый результат после сортировки
печатает:
title
author
description
path
7. Ограничения текущей реализации
Ниже только то, что прямо видно из кода.

Нет извлечения текста из PDF: pdf_parser.py возвращает только title=path.stem.
Нет парсеров для .txt, .djvu, .doc, .docx, хотя эти расширения участвуют в сканировании.
Нет сохранения raw_text в индекс: в SQLite хранится description, но не полный текст.
Нет полнотекстового поиска по содержимому книги: поиск идёт только по name, title, author.
Нет embeddings.
Нет semantic search.
Нет отдельной модели/таблицы для фрагментов текста.
Нет ранжирования по релевантности кроме сортировки по названию.
Нет нормализации/валидации пользовательского ввода в CLI сверх минимальных проверок аргументов.
Нет транзакционной пакетной логики поверх одного INSERT OR REPLACE на книгу.
Генерация описания зависит от внешнего локального сервиса http://localhost:11434/api/generate; при ошибке просто возвращается None.
В main.py есть прямой вывод отладочной информации:
print(book_indexer.__file__)
print("cli started")
В текущем EPUB-парсере есть print(...) отладочного вывода внутри _extract_spine_text().
В build_book() исключения парсера подавляются общим except Exception, после чего result = None.
Статус "partial" у парсеров используется, но отдельной обработки этого статуса в storage/CLI нет.
JSON-хранилище в index.py существует, но в CLI-потоке не используется.


04/04/2026
🧠 Саммари состояния проекта
🎯 Общий уровень

Проект перешёл из:

индексатор файлов

в:

локальная RAG-система (v1)
⚙️ Что реализовано
1. Индексация
сканирование каталога
поддержка:
fb2 / fb2.zip
epub (улучшено)
pdf (stub)
метаданные:
title
author
description (через Ollama)
2. EPUB (ключевой апгрейд)
фильтрация:
toc / nav / contents
отсечение мусора:
короткие куски
ограничение:
первые 3–5 частей книги
результат:
берётся начало книги (релевантный текст)
3. raw_text
добавлено в:
модель Book
SQLite (books.raw_text)
сохраняется при парсинге
4. chunks
разбиение текста:
chunk_size ≈ 800
overlap ≈ 150
хранение:
отдельная таблица book_chunks
5. embeddings
модель: nomic-embed-text (Ollama)
хранение:
book_chunks.embedding
считаются:
только для added / updated
6. semantic search
cosine similarity
keyword boost (ограниченный)
фильтрация коротких чанков
возвращает top-N
7. RAG (ask2)
query → embedding → chunks → context → LLM → answer
используется mistral
prompt с ограничением “не выдумывать”
вывод:
ответ
источники
📊 Текущее поведение
✔ работает:
система отвечает на вопросы
есть связный ответ
нет случайного мусора в ответе
есть trace (sources)
❗ проблемы:
retrieval шумный
художественные тексты в топе
embedding “размытый”
не отличает определение от нарратива
нет reranking
LLM работает с неидеальным контекстом
🧠 Ключевой инсайт (важно зафиксировать)

Ты попробовал:

фильтры ❌ (слишком жёстко)
бусты ⚠️ (легко ломают ранжирование)

👉 и упёрся в:

ограничение retrieval без rerank

🚀 Логичный следующий шаг (на завтра)

Не усложнять scoring.

👉 сделать:

LLM reranking (очень сильный апгрейд)

Идея:

1. взять top-10 chunks
2. спросить LLM:
   "какие из них отвечают на вопрос?"
3. взять top-3
4. только их отправить в финальный prompt

👉 это обычно даёт x2–x5 к качеству

📍 Альтернативные ветки

Если не rerank:

1. улучшить embeddings
другая модель (например bge)
2. фильтр по книге
boost по title
3. сохранить chunk_index
приоритет начала книги
🧩 Итог

Ты уже собрал:

рабочую локальную knowledge base с AI-доступом

Это не прототип — это уже основа системы.

Отдохни, а завтра можно аккуратно сделать следующий шаг без “переламывания” архитектуры.


