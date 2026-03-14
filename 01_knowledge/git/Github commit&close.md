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