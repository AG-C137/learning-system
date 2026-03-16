# Git workflow on multiple machines

Цель: безопасно работать с одним проектом на нескольких компьютерах.

Пример:

Linux #1
Linux #2
Windows
GitHub (origin)

GitHub — источник истины  
Каждая машина — локальная копия

---

## 1. Общий принцип

Никогда не переносим проект вручную.

НЕ делать:

- копирование папок
- архивы
- флешки

Всегда:

git push
git pull

---

## 2. Начало работы на новой машине

1. clone

git clone git@github.com:USER/learning-system.git
cd learning-system

2. выбрать ветку

git branch -a

git switch feature/branch-name

или

git switch -c feature/branch-name origin/feature/branch-name

3. создать venv

python3 -m venv .venv
source .venv/bin/activate

4. установить зависимости (если есть)

pip install -r requirements.txt

---

## 3. Правильный цикл работы

Каждый раз перед работой:

git pull

Работа:

edit files

Сохранить:

git add .
git commit -m "message"

Отправить:

git push

---

## 4. Переключение между машинами

Машина 1:

git push

Машина 2:

git pull

Продолжаем работу.

---

## 5. Работа с feature ветками

Никогда не работаем в main.

Создать ветку:

git switch -c feature/topic

Отправить:

git push -u origin feature/topic

На другой машине:

git pull
git switch feature/topic

---

## 6. Проверка текущей ветки

git branch

Текущая отмечена *

---

## 7. Проверка удалённых веток

git branch -a

или

git branch -r

---

## 8. Если push не проходит

Ошибка:

rejected

Правильно:

git pull
git push

---

## 9. SSH ключи

Каждая машина имеет свой ключ.

~/.ssh/

GitHub хранит несколько ключей.

Это нормально.

---

## 10. venv не хранится в git

.gitignore:

.venv/
__pycache__/

venv создаётся на каждой машине заново.

---

## 11. Признаки правильной среды

✔ git pull работает
✔ git push работает
✔ ssh работает
✔ venv активен
✔ python из .venv
✔ правильная ветка

Среда воспроизводима.