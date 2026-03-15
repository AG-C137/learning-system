Содержимое файла
# Dev setup on new machine (Linux / Windows)

Цель: воспроизвести проект с GitHub на новой машине.

Общий принцип:

GitHub = источник истины  
Машина = локальная копия  
venv = создаётся заново  

---

## 1. Установить инструменты

| Шаг | Linux | Windows |
|------|--------|-----------|
| Git | apt install git | install Git for Windows |
| Python | apt install python3 | python.org installer |
| venv | apt install python3-venv | встроен |
| VSCode | apt install code | install VSCode |

---

## 2. Клонировать репозиторий


git clone https://github.com/USER/learning-system.git

cd learning-system


Проверка:


git branch -a


---

## 3. Переключиться на нужную ветку


git switch feature/project-structure-basics


если не существует локально:


git switch -c feature/project-structure-basics origin/feature/project-structure-basics


---

## 4. Настроить git пользователя


git config --global user.name "Name"
git config --global user.email "email"


Проверка:


git config --list


---

## 5. Настроить SSH

Создать ключ:


ssh-keygen -t ed25519 -C "github"


Показать ключ:

Linux:


cat ~/.ssh/id_ed25519.pub


Windows:


type %USERPROFILE%.ssh\id_ed25519.pub


Добавить в GitHub → SSH keys

Проверка:


ssh -T git@github.com


Ожидается:


Hi USERNAME! You've successfully authenticated


---

## 6. Создать виртуальную среду

Linux:


python3 -m venv .venv


Windows:


python -m venv .venv


---

## 7. Активировать venv

Linux:


source .venv/bin/activate


Windows PowerShell:


.venv\Scripts\activate


Windows CMD:


.venv\Scripts\activate.bat


Проверка:


python -c "import sys; print(sys.executable)"


---

## 8. Установить зависимости (если есть)

Если есть файл:


requirements.txt


то:


pip install -r requirements.txt


Если нет — пропустить.

---

## 9. Проверить перевод строк (Windows)

Рекомендуется:


git config --global core.autocrlf input


Проверка:


git config --global core.autocrlf


---

## 10. Проверка готовности

✔ git pull работает  
✔ git push работает  
✔ ssh работает  
✔ venv активируется  
✔ python из .venv  
✔ нужная ветка выбрана  

Среда готова.
Как правильно добавить в проект

На любой машине:

git switch -c feature/knowledge-dev-setup

создать файл

01_knowledge/environment/dev_setup_windows_linux.md

добавить

git add .
git commit -m "knowledge: dev setup linux windows"
git push

потом PR.