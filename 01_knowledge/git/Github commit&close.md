📍Шаг 1 — проверить где мы сейчас
git branch

Должно быть что-то вроде:

* feature/import-test
  main

Если ты всё ещё в feature — хорошо.

Если нет — надо вернуться.

📍Шаг 2 — проверить изменения
git status

Если есть изменения:

git add .
git commit -m "import mechanics experiment"

Коммит должен быть осмысленный, по теме.

✔ правильно

import mechanics experiment

✔ ещё лучше

experiment: python import mechanics, sys.path test

❌ плохо

fix
update
123

Дисциплина коммитов = дисциплина мышления.

📍Шаг 3 — push feature ветки
git push

или если первый push

git push -u origin feature/import-test
📍Шаг 4 — Pull Request

На GitHub / GitLab:

открыть PR

проверить diff

merge → main

Это часть обучения, не пропускаем.

Даже если ты один.

📍Шаг 5 — вернуться в main

После merge:

git checkout main
git pull

Проверка:

git branch

Должно быть

* main
📍Шаг 6 — удалить feature ветку (важная привычка)

Локально:

git branch -d feature/import-test

Удалённо (не обязательно, но хорошо):

git push origin --delete feature/import-test

GitHub уже удалил ветки, но локальный Git ещё помнит старые remote-refs.
Нужно сделать очистку ссылок.

Это как раз ещё один уровень понимания среды.

📍Почему так происходит

Git хранит remote-ветки локально как ссылки:

origin/feature/roadmap-depth-model
origin/feature/vibecode-base

Даже если на GitHub их уже нет.

Пока ты не сделаешь обновление, Git считает, что они есть.

📍Правильная команда очистки
git fetch --prune

или короче

git remote prune origin

Обе команды нормальные, но чаще используют первую.

📍Что делает fetch --prune
fetch  → обновляет remote refs
prune  → удаляет несуществующие ветки

То есть:

GitHub → список веток
Git → обновляет локальные ссылки
📍После этого проверить
git branch -r

Должно остаться:

origin/main
origin/HEAD -> origin/main

Мы закрыли цикл правильно:

feature → commit → push

PR → merge

pull → sync

delete local

delete remote

prune


Шаг 1 — новая ветка

По правилам системы:

git checkout -b feature/import-mechanics
git checkout -b feature/level1-execution-model