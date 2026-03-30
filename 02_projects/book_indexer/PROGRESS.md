Book Indexer — Checkpoint: Incremental + Cleanup + Summary
Архитектура

Слои строго разделены:

scan → build → storage → CLI (orchestration)
scan — находит файлы
build — создаёт Book и определяет статус
storage — SQLite (upsert, mark, cleanup)
CLI — оркестрация + агрегация статистики
Incremental поведение (инвариант)
файл считается unchanged, если size + mtime не изменились
такие файлы:
не пересобираются
не записываются повторно
НО остаются в базе
Cleanup (mark-and-sweep)

Используется схема:

current_run — id запуска
last_seen — отметка последнего появления

Flow:

новые/изменённые → upsert + last_seen
все найденные файлы → mark_seen_bulk

cleanup:

DELETE WHERE last_seen < current_run
Критический фикс

Исправлено:

skip-файлы теперь проходят через mark_seen_bulk
устранён баг с несовпадением путей (нормализация)
Logging / Summary

Добавлена сводка выполнения:

+ added
~ updated
- removed
= unchanged

Где:

added — новые файлы
updated — изменённые
unchanged — пропущенные (skip)
removed — удалённые через cleanup
Распределение ответственности
build_book(path, existing_meta)
решает: added / updated / unchanged
CLI:
делает lookup (get_book_file_info)
считает unchanged
агрегирует статистику
storage:
не знает про skip
возвращает:
added / updated из save_index_sqlite
removed из cleanup_missing_books
Текущее состояние

✔ incremental работает
✔ cleanup безопасен
✔ skip не ломает базу
✔ summary отражает реальное состояние
✔ архитектура сохранена

Статус

production-safe core + observability