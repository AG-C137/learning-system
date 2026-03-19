
проверить где мы сейчас
```
git branch
```
Должно быть что-то вроде:
```
* feature/import-test
  main
```
Если ты всё ещё в feature — хорошо.

Если нет — надо вернуться.

📍Шаг 2 — проверить изменения

```git status```

Если есть изменения:
```
git add .
git commit -m "import mechanics experiment"

```
Коммит должен быть осмысленный, по теме.

📍Шаг 3 — push feature ветки
```
git push

# или если первый push

git push -u origin feature/import-test
git push -u origin feature/level1-execution-model
git push -u origin feature/level1-sys-modules
git push -u origin feature/level2_package_install
```
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
```
git branch -d feature/import-test
git branch -d feature/level1-import-system
git branch -d feature/project-structure-basics
```
Удалённо (не обязательно, но хорошо):
```
git push origin --delete feature/import-test
```
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
```
git fetch --prune

# или короче

git remote prune origin
```
Обе команды нормальные, но чаще используют первую.

📍После этого проверить
```
git branch -r
```
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
```
git checkout -b feature/import-mechanics
git checkout -b feature/level1-execution-model
git checkout -b feature/level1-import-system


git add .
git commit -m "level1: import system experiments"
git checkout main
git merge feature/level1-import-system
git checkout -b feature/project-structure-basics
```
✅ 1. Проверка — есть ли коммиты локально

В корне проекта:

git status

Если увидишь:

nothing to commit, working tree clean

→ всё закоммичено.

Если нет — нужно коммитить.

Проверка истории:

git log --oneline --graph

Ты должен увидеть коммиты из

feature/level1-import-system
✅ 2. Проверка — отправляли ли в GitHub
git branch -vv

Если увидишь:

feature/level1-import-system  abc1234 [origin/feature/level1-import-system]

→ ветка есть на GitHub

Если:

feature/level1-import-system  abc1234

без origin → только локально.

Ещё проверка:

git remote -v

Должно быть что-то вроде:

origin  git@github.com:...

Если remote есть, но push не делали — всё локально.

✅ 3. Как правильно по твоей системе

По твоим правилам Learning System:

feature → commit → PR → merge → push

Мы пока сделали:

feature → commit

Но не сделали:

push
PR
merge

Это нормально, но лучше закрывать цикл.

✅ 4. Правильное закрытие блока Import System

Если всё готово:

git checkout feature/level1-import-system
git add .
git commit -m "level1: import mechanics experiments"
git push -u origin feature/level1-import-system

Потом:

git checkout main
git merge feature/level1-import-system
git push

(или через PR, как ты делал раньше)

✅ 5. После этого можно открывать новую ветку
git checkout -b feature/project-structure-basics

И это будет чистый переход на новый блок.

### Если забыл открыть новую ветку

✅ Правильное решение (без потери коммитов)

Мы не будем удалять,
мы перенесём текущее состояние в новую ветку.

Это правильная инженерная практика.

✅ Шаг 1 — проверить статус
git status

Если есть незакоммиченные изменения → сначала коммит.

git add .
git commit -m "level2 step2 dependency direction"
✅ Шаг 2 — создать ветку из текущего состояния

Сейчас ты стоишь в main, но с нужным кодом.

Создаём ветку:

git checkout -b feature/level2-dependency-direction

Теперь:

main ──┐
       └── feature/level2-dependency-direction (текущий)

Все изменения уже в ветке.

Это нормально.

✅ Шаг 3 — вернуть main назад

Теперь нужно очистить main.

Переключаемся:

git checkout main

И откатываем к origin/main:

git reset --hard origin/main

Теперь:

main = чистый
feature = с работой

Это именно то, что нужно.

✅ Шаг 4 — проверить
git branch

Должно быть:

main
* feature/level2-dependency-direction

(если нет — переключись обратно)

git checkout feature/level2-dependency-direction
✅ Шаг 5 — дальше всё как правильно
git push origin feature/level2-dependency-direction

Потом PR.

✅ Важно — это нормальная ситуация

Так работают все.

Важно не не ошибаться, а:

уметь восстановить workflow

Это и есть Level 0 mastery.

▶ Следующий шаг (после фикса ветки)

Мы пойдём в

Level 2 — Step 3
Separation of Concerns

Это следующий ключ архитектуры.

удалять локально?

Да, но правильный порядок важен, чтобы не удалить работу.
Сейчас у тебя есть:

main (испорчен)
feature/level2-dependency-direction (нужный)

Нужно:

оставить feature
очистить main

Удалять ничего пока не нужно.
Сначала убедимся, что всё сохранено.

✅ Шаг 1 — проверить ветки
git branch

Должно быть:

main
feature/level2-dependency-direction

Перейди в feature:

git checkout feature/level2-dependency-direction
✅ Шаг 2 — убедиться что коммиты есть
git log --oneline

Должен быть твой коммит типа:

level2 step2 dependency direction

Если есть → всё безопасно.

✅ Шаг 3 — теперь можно чинить main

Переключаемся:

git checkout main

Откатываем:

git reset --hard origin/main

Теперь main снова чистый.

Это НЕ удаляет feature.

✅ Шаг 4 — удалять ли локально?

Удалять нужно только если есть лишняя ветка.

Проверка:

git branch

Если есть только:

main
feature/level2-dependency-direction

то ничего удалять не надо.

Удаление нужно только если случайно создал ещё ветки.

Удаление делается так:

git branch -d имя_ветки
✅ Когда удаляют ветку

После merge.

Правильный цикл:

feature → commit
feature → push
PR → merge
delete feature

Сейчас ты на стадии:

feature → commit ✔
main → исправили ✔
дальше push
✅ Следующий правильный шаг
git checkout feature/level2-dependency-direction
git push origin feature/level2-dependency-direction

После этого будет чистый workflow.

это все сделал, сделал pr и удалил ветку на гитхабе

Отлично. Это значит ты прошёл полный правильный цикл Level 0 workflow:

feature branch
commit
push
pull request
merge
delete branch
sync main

Это именно тот процесс, который должен стать автоматическим.

Теперь важно сделать последний шаг, который часто забывают.

После удаления ветки на GitHub
локальная ветка обычно остаётся.

✅ Шаг 1 — проверить локальные ветки
git branch

Если увидишь:

main
feature/level2-dependency-direction

то локальную ветку можно удалить.

✅ Шаг 2 — удалить локальную feature
git branch -d feature/level2-dependency-direction

Git может сказать:

Deleted branch feature/level2-dependency-direction

Если скажет:

not fully merged

тогда:

git branch -D feature/level2-dependency-direction

Но обычно -d хватает после PR.

✅ Шаг 3 — обновить main

Это уже инженерный workflow.

