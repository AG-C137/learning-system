# Book Indexer — progress summary

Repo: learning-system  
Branch: feature/book_indexer  
Project: 02_projects/book_indexer  

## Current state

## Book Indexer — Summary (checkpoint)

### Архитектура

Проект построен по слоям:

* scan → находит файлы
* build → создаёт Book + решает skip (size + mtime)
* storage → SQLite

Слои не смешиваются.

---

### Текущие возможности

* сканирование директории
* registry парсеров
* модель Book
* SQLite storage
* CLI (book-index)
* editable install

---

### Incremental поведение (инвариант)

* файлы не перерабатываются, если size + mtime не изменились
* при этом они ДОЛЖНЫ оставаться в базе

---

### Реализован cleanup (mark-and-sweep)

Добавлено:

* поле last_seen
* run_id (current_run)

Логика:

1. каждый запуск генерирует current_run
2. новые/изменённые файлы → upsert + last_seen
3. ВСЕ файлы → mark_seen_bulk (обновление last_seen)
4. cleanup:
   DELETE WHERE last_seen < current_run

---

### Критический фикс

Исправлена ошибка:

* раньше skip-файлы не обновляли last_seen
* это приводило к их удалению

Решение:

* добавлен mark_seen_bulk(paths, ...)

---

### Текущее состояние

✔ incremental работает
✔ cleanup безопасен
✔ повторные запуски стабильны
✔ удаление/добавление файлов корректно отражается

Проект достиг уровня "production-safe core".

---

### Следующий шаг

Добавить логирование изменений:

* added
* updated
* removed
* unchanged

Без изменения архитектуры.
