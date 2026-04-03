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