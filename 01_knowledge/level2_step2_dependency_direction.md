✅ Итог Step 2 — Dependency Direction
Главное правило
Зависимости идут сверху вниз

или

Upper layer imports lower layer
Lower layer must NOT import upper layer
✅ Правильный граф
run.py
  ↓
cli
  ↓
services
  ↓
core
  ↓
config

Допустимо:

cli → services
cli → config
services → core
services → config
core → config

Запрещено:

core → services
core → cli
config → core
config → services
config → cli
services → cli
✅ Почему это важно (механика Python)

Импорт в Python = выполнение файла.

import module
→ Python выполняет module.py

Если есть цикл:

A → B → C → A

то Python попадает в ситуацию:

A ещё не загрузился
но его уже импортируют

и появляется:

partially initialized module

Это не баг.

Это следствие модели выполнения Python.

✅ Почему Config должен быть самым нижним

Config — это:

данные среды
настройки
константы
пути
env

Он должен быть независим.

Правильно:

все знают config
config не знает никого

Это правило есть в:

Django settings

FastAPI config

Linux kernel config

build systems

compilers

AI pipelines

✅ Почему CLI должен быть сверху

CLI — это интерфейс.

Сегодня:

CLI

Завтра:

HTTP API

Потом:

GUI

Потом:

Telegram bot

Если core знает CLI → всё ломается.

Поэтому:

CLI → Service → Core → Config

Это стандарт индустрии.