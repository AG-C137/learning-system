1. Что делает python pkg/run.py

Python считает, что ты запускаешь файл, а не пакет.

Поэтому:

sys.path[0] = directory of script

Скрипт лежит тут:

import_test/pkg/run.py

Значит:

sys.path[0] = import_test/pkg

И Python ищет pkg внутри:

import_test/pkg/pkg

Его нет → ошибка.

Вот почему:

ModuleNotFoundError: No module named 'pkg'

Это логично.

2. Что делает python -m pkg.run

Это совершенно другой режим.

Python запускает модуль внутри пакета.

Он делает:

найти pkg в sys.path

А sys.path[0] теперь:

import_test

Поэтому:

import_test/pkg

находится.

И всё работает.

Это правильный режим для пакетов.

3. Главное правило архитектуры Python

❗ Если код внутри пакета — запускать через -m

Правильно:

python -m pkg.run

Неправильно:

python pkg/run.py

Во всех серьёзных проектах используют -m.

4. Почему это важно для реальных проектов

Это влияет на:

CLI

pytest

FastAPI

Django

setuptools

poetry

uv

pip

entry points

Все они используют режим пакета.

5. Связь с тем, что мы уже видели в vibecode

Помнишь:

python vibecode-prep/main.py

vs

python -m vibecode_prep.main

Это тот же механизм.

Мы не случайно туда пришли.

6. Фиксируем знание (по системе обучения)

Нужно сделать файл:

01_knowledge/import_mechanics.md

С тем, что мы выяснили:

sys.path

script vs module

-m

package context

cwd vs script dir

Это обязательный шаг по модели.