# Python Import Rules

Level: 1 — Python Internals  
Topic: import system

---

## 1. Главное правило

Python импортирует **модули**, а не файлы.

Файл становится модулем, если он находится в одном из путей:

- current working directory
- PYTHONPATH
- standard library
- site-packages

Проверка:

```python
import sys
print(sys.path)
```
## 2. Что такое модуль и пакет

Модуль:

file.py

Пакет:

```pkg/
    __init__.py
    mod.py
``` 

Импорт:

import pkg.mod
## 3. Абсолютный импорт (рекомендуется)
```
import pkg.mod
from pkg import mod
from pkg.mod import func
```

Свойства:

стабилен

работает из любой точки

используется в production

используется при запуске через -m

Правило:

Использовать абсолютный импорт по умолчанию

## 4. Относительный импорт
```
from . import mod
from .sub import mod2
from ..core import utils
```

Работает только если:

модуль внутри пакета

есть init.py

запуск через -m

package != None

Не работает:

python pkg/mod.py

Работает:

python -m pkg.mod

## 5. Script mode vs Module mode

``` 
Script mode:

python file.py
__name__ = "__main__"
__package__ = None

Module mode:

python -m pkg.mod
__name__ = "__main__"
__package__ = "pkg"
```


Относительный импорт требует package context.

## 6. Правило запуска

Нельзя запускать модули внутри пакета.

Неправильно:

python pkg/mod.py

Правильно:

python -m pkg.mod

или

python run.py

## 7. src layout

Рекомендуемая структура:
```

project/
    run.py
    src/
        app/
            __init__.py
            main.py

Запуск:

python run.py

или

python -m app.main
``` 

если src в PYTHONPATH.

## 8. Частые ошибки

ModuleNotFoundError
→ модуль не в sys.path

attempted relative import
→ script mode

cannot import name
→ cyclic import

работает / не работает
→ разный cwd

## 9. Золотые правила

использовать absolute import

запускать через -m

использовать src layout

не запускать файлы внутри пакета

понимать sys.path

понимать package

понимать name

## 10. Вывод

Import system зависит от:

cwd

sys.path

package context

способа запуска

Понимание этого — ключ к Python Internals.