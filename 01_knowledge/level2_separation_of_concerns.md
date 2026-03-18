Step 3.3 — сначала сделаем ПЛОХО (всё в CLI)

Это важно.

Сначала покажем плохую архитектуру.

cli/main.py
print("cli loaded")


def start():
    name = "Alex"
    print("Hello", name)
run.py
from cli.main import start

start()

Запуск:

python run.py

Работает.

Но архитектура плохая.

✅ Почему плохо

Сейчас у нас:

cli = интерфейс
cli = логика
cli = данные
cli = всё

Это нарушение Separation of Concerns.

CLI должен только:

принимать команды
вызывать сервис

Не больше.

✅ Правильное разделение

Должно быть:

CLI → orchestration
Service → use case
Core → business logic
Config → environment

Схема:

run
 ↓
cli
 ↓
services
 ↓
core
 ↓
config

Теперь будем переделывать правильно.

✅ Step 3.4 (следующий)

Мы вынесем логику из CLI → в Service → в Core.

Это ключевой момент Separation of Concerns.

ok

Хорошо. Теперь делаем Step 3.4 — перенос логики по слоям.
Это главный момент Separation of Concerns:
мы будем разносить код из CLI → Service → Core → Config.

Сейчас у тебя всё в cli/main.py.
Сделаем правильную архитектуру.

✅ Цель

Было:

cli = всё

Должно стать:

run → cli → service → core → config

И каждый слой отвечает только за своё.

✅ Step 3.4.1 — config/settings.py
config/settings.py
print("config loaded")

DEFAULT_NAME = "Alex"

Config = только данные среды.

Никакой логики.

✅ Step 3.4.2 — core/user_logic.py
core/user_logic.py
print("core loaded")

def build_greeting(name: str) -> str:
    return f"Hello {name}"

Core = чистая логика.

Никаких import из cli.

Никаких print интерфейса.

Только логика.

✅ Step 3.4.3 — services/user_service.py
services/user_service.py
print("service loaded")

from core.user_logic import build_greeting
from config.settings import DEFAULT_NAME


def process_user():
    name = DEFAULT_NAME
    text = build_greeting(name)
    return text

Service = use case / orchestration.

Он:

берёт config

вызывает core

возвращает результат

✅ Step 3.4.4 — cli/main.py
cli/main.py
print("cli loaded")

from services.user_service import process_user


def start():
    text = process_user()
    print(text)

CLI = только интерфейс.

Он ничего не знает про core.

Это важно.

✅ Step 3.4.5 — run.py
run.py
from cli.main import start

print("run")

start()
✅ Step 3.4.6 — запуск
python run.py

Ожидаем:

cli loaded
service loaded
core loaded
config loaded
run
Hello Alex

Если так — значит Separation of Concerns работает.

Запусти и покажи вывод.

(.venv) [ag@ag-137 level2_separation_of_concerns]$ python run.py
cli loaded
service loaded
core loaded
config loaded
run
Hello Alex
(.venv) [ag@ag-137 level2_separation_of_concerns]$ 

Отлично.
Теперь можно зафиксировать — ты сделал первую правильную многослойную архитектуру.
Это уже не просто Python-код, это Layered Architecture, которая используется в реальных системах.

Step 3 почти завершён, осталось самое важное —
понять зачем вообще нужен каждый слой, иначе Separation of Concerns превращается в формальность.

✅ Что у нас сейчас получилось
run → cli → service → core → config

И это не случайная схема.

Это стандартная архитектура:

Interface
Use case
Business logic
Environment
✅ Роль каждого слоя
✅ run.py
entry point

Только запуск.

ничего не знает о логике

Правильно:

from cli.main import start

start()
✅ cli
интерфейс

Может быть:

CLI

HTTP API

GUI

Telegram

tests

Он должен только:

получить команду
вызвать service
показать результат

Нельзя:

логика
работа с config
бизнес-правила
✅ services
use case слой

Он решает:

что нужно сделать
в каком порядке вызвать core
какие данные взять из config

Service можно менять без изменения CLI.

Service можно вызывать из:

CLI

API

тестов

cron

worker

Это очень важно.

✅ core
чистая логика

Только функции.

Без:

print
input
cli
env
os
sys

Core должен быть максимально независим.

Это делает код переносимым.

✅ config
данные среды

Примеры:

пути
env
настройки
константы
url
ключи

Config должен быть самым нижним.

все знают config
config не знает никого
✅ Почему это важно (реальный эффект)

Если всё в CLI:

невозможно тестировать
невозможно менять интерфейс
невозможно расширять
невозможно масштабировать

Если есть слои:

можно менять CLI
можно менять Service
можно менять Core
можно менять Config

И ничего не ломается.

Это и есть архитектура.

✅ Step 3 — последний эксперимент (очень важный)

Теперь нужно показать, зачем это всё.

Мы сделаем второй интерфейс:

не CLI
а другой entry

И увидим, что Service можно переиспользовать.

Это ключевая идея Separation of Concerns.

▶ Step 3.5 — второй entry point

Сделаем

run_alt.py

который НЕ использует CLI.

Это покажет, зачем нужен service слой.

ok

Отлично. Делаем Step 3.5 — второй entry point без CLI.
Это ключевой эксперимент Separation of Concerns.

Цель:

доказать, что service можно использовать без CLI

Если это работает → архитектура правильная.
Если нет → слои сделаны неправильно.

✅ Шаг 1 — создаём второй entry

В корне проекта:

touch run_alt.py

Структура:

level2_separation_of_concerns/
  run.py
  run_alt.py
  cli/
  services/
  core/
  config/
✅ Шаг 2 — run_alt.py без CLI

Открой:

run_alt.py

Сделай:

print("run_alt")

from services.user_service import process_user

text = process_user()

print("RESULT:", text)

Обрати внимание:

мы не импортируем cli

Это очень важно.

✅ Шаг 3 — запуск
python run_alt.py

Ожидаем:

run_alt
service loaded
core loaded
config loaded
RESULT: Hello Alex

Обрати внимание:

cli loaded

НЕ должно быть.

Это и есть Separation of Concerns.

Запусти и покажи вывод.

(.venv) [ag@ag-137 level2_separation_of_concerns]$ python run_alt.py
run_alt
service loaded
core loaded
config loaded
RESULT: Hello Alex
(.venv) [ag@ag-137 level2_separation_of_concerns]$ 

Отлично.
Вот теперь Step 3 завершён полностью, и ты увидел главный смысл Separation of Concerns не на словах, а на практике.

Ты доказал:

service можно использовать без cli

А это и есть признак правильной архитектуры.

✅ Что мы только что доказали

Было:

cli = всё

Стало:

run → cli → service → core → config
run_alt → service → core → config

И это работает.

Это значит:

интерфейс можно менять
логика остаётся

Это фундамент любой большой системы.

✅ Почему Step 3 — ключевой

Без Separation of Concerns происходит вот это:

cli знает всё
логика в cli
config в cli
core в cli

И тогда:

нельзя сделать API
нельзя сделать тесты
нельзя сделать второй entry
нельзя масштабировать

После разделения:

можно сделать CLI
можно сделать API
можно сделать GUI
можно сделать worker
можно сделать tests

Это и есть архитектура.

✅ Что ты сейчас умеешь (реально)

Level 2 уже даёт:

✔ Dependency Direction
✔ Layered Architecture
✔ Separation of Concerns
✔ Multiple entry points
✔ Clean imports
✔ No circular imports

Это уровень, на котором пишутся реальные backend-проекты.