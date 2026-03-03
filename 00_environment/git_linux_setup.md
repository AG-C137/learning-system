# Резюме: Настройка среды разработки (ALT Linux + VS Code + Git + GitHub)

## 1. Установка VS Code в ALT Linux

### Проблема

Стандартная команда `epm install code` устанавливала не тот пакет (ruby-gem), так как ALT Linux использует apt-rpm, а не yum.

### Решение

1. Скачать официальный RPM:

   ```bash
   wget https://update.code.visualstudio.com/latest/linux-rpm-x64/stable -O code.rpm
   ```
2. Установить через epm:

   ```bash
   sudo epm install ./code.rpm
   ```
3. Проверить установку:

   ```bash
   code --version
   ```

Итог: VS Code установлен и работает.

---

## 2. Установка и настройка Git

### Установка

```bash
sudo epm install git
```

Проверка:

```bash
git --version
```

### Настройка пользователя

```bash
git config --global user.name "Имя"
git config --global user.email "email@example.com"
```

Проверка:

```bash
git config --global --list
```

---

## 3. Создание первого проекта

1. Создана папка проекта (`test-project`).
2. Инициализирован репозиторий через VS Code.
3. Создан файл `README.md`.
4. Выполнен первый commit.

Проверка истории:

```bash
git log --oneline
```

Освоена модель Git:

Изменение → Stage → Commit → История

---

## 4. Подключение GitHub

1. Создан публичный репозиторий на GitHub.
2. Добавлен remote:

   ```bash
   git remote add origin https://github.com/USERNAME/test-project.git
   ```
3. Проверка:

   ```bash
   git remote -v
   ```
4. Первый push:

   ```bash
   git branch -M main
   git push -u origin main
   ```

Итог: локальный и удалённый репозиторий синхронизированы.

---

## 5. Что освоено

* Установка ПО в ALT Linux через epm
* Разница между нативной установкой и Flatpak
* Базовая архитектура Git
* Работа с VS Code как с проектной средой
* Связка локального репозитория с GitHub

---

## 6. Текущий уровень

Среда разработки полностью готова:

Linux → VS Code → Git → GitHub

Можно переходить к:

* веткам
* pull / pull request
* рабочему процессу разработки
* подготовке к курсу VibeCode

---

Документ создан как базовый артефакт проекта "Изучение проектов".
