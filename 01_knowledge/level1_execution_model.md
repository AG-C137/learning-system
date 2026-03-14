# Level 1 — Execution Model

## 1. Общая модель выполнения Python

Python выполняет не файл, а модуль.

Схема:

.py file
→ module object
→ module.__dict__ (namespace)
→ exec(code, namespace)


## 2. Создание модуля при запуске

При запуске:

python file.py

Python делает:

1. Создаёт module object
2. Устанавливает __name__ = "__main__"
3. Добавляет модуль в sys.modules
4. Создаёт namespace (dict)
5. Выполняет код файла в namespace


## 3. sys.modules

sys.modules — это словарь всех загруженных модулей.

Ключ = имя модуля  
Значение = module object

Пример:

import sys

print(__name__ in sys.modules)
print(sys.modules[__name__])


## 4. Namespace модуля

Каждый модуль имеет namespace:

module.__dict__

Все переменные записываются туда.

Пример:

x = 10

↓

module.__dict__["x"] = 10


## 5. globals()

globals() возвращает namespace текущего модуля.

globals() is module.__dict__ == True


## 6. Выполнение кода

Код модуля выполняется так:

exec(code, module.__dict__)


## 7. Важные выводы

- Python всегда работает через модули
- файл — это только источник кода
- namespace — обычный dict
- import использует sys.modules
- выполнение происходит внутри namespace модуля


## 8. Формула execution model

file → module → namespace → execution