1. Module vs Package
Module
mod.py

Импорт:

import mod
Package
pkg/
    __init__.py
    mod.py

Импорт:

import pkg.mod

📌 Package = папка с __init__.py

(в современных версиях можно без него, но мы используем — для понимания)

2. Сделаем эксперимент

В твоём проекте:

src/
    main.py

Создай:

src/
    pkg/
        __init__.py
        mod.py
mod.py
print("pkg.mod loaded")

value = 123
init.py
print("pkg init loaded")
main.py
import pkg.mod

print(pkg.mod.value)

Запуск:

python src/main.py

Ожидаем:

pkg init loaded
pkg.mod loaded
123
3. Почему выполняется __init__.py

Когда Python делает:

import pkg.mod

Он делает:

1. найти pkg
2. загрузить pkg
3. выполнить __init__.py
4. найти mod
5. загрузить mod

Схема:

import pkg.mod
   ↓
pkg → __init__.py
   ↓
pkg.mod → mod.py

Это важно для понимания.

4. Проверим sys.modules

Добавь в main.py:

import sys
import pkg.mod

print("pkg in cache:", "pkg" in sys.modules)
print("pkg.mod in cache:", "pkg.mod" in sys.modules)

Увидишь:

True
True

Значит:

sys.modules["pkg"]
sys.modules["pkg.mod"]

Оба модуля лежат в cache.

5. Почему иногда import ломается

Если структура такая:

project/
    main.py
    pkg/
        mod.py

то может работать…

а может нет.

Почему?

→ зависит от sys.path[0]

Вот зачем мы делаем:

project/
    src/
        pkg/

Это правильная архитектура.

6. Главное понимание Level 1 (база закрыта)

Ты теперь понимаешь:

тема	понимаешь?
execution model	✅
name	✅
sys.modules	✅
circular import	✅
sys.path	✅
package	✅
init	✅
import cache	✅

Это базовое ядро Python internals.