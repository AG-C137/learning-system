# Python Import & Execution Model

## 1. Как Python ищет модули

При `import module` Python:

1. Проверяет `sys.modules`
2. Ищет в `sys.path`
3. Загружает файл
4. Создаёт module object
5. Сохраняет в `sys.modules`

```
import → sys.modules → sys.path → load → cache
```

---

## 2. sys.path

`sys.path` — список директорий, где Python ищет модули.

Ключевой элемент:

```
sys.path[0]
```

Зависит от режима запуска.

| Запуск            | sys.path[0]     |
| ----------------- | --------------- |
| python file.py    | directory файла |
| python -m pkg.mod | project root    |
| python REPL       | current dir     |

---

## 3. Script vs Module

### Script mode

```
python pkg/run.py
```

```
__name__ = "__main__"
__package__ = None
sys.path[0] = pkg/
```

Python считает файл обычным скриптом.

Импорты пакета могут ломаться.

---

### Module mode

```
python -m pkg.run
```

```
__name__ = "__main__"
__package__ = "pkg"
sys.path[0] = project root
```

Python запускает модуль внутри пакета.

Импорты работают правильно.

---

### Import mode

```
import pkg.mod
```

```
__name__ = "pkg.mod"
__package__ = "pkg"
```

Файл загружен как модуль.

---

## 4. Правило для пакетов

Если код внутри пакета → запускать через `-m`

Правильно:

```
python -m pkg.run
```

Неправильно:

```
python pkg/run.py
```

---

## 5. **name**

```
__name__ == "__main__"
```

только у запускаемого модуля.

Импортируемый модуль:

```
__name__ = pkg.mod
```

Используется для точки входа.

```
if __name__ == "__main__":
    main()
```

Позволяет файлу быть:

* скриптом
* модулем
* библиотекой

---

## 6. **package**

Определяет контекст пакета.

| режим  | **package** |
| ------ | ----------- |
| script | None        |
| -m     | pkg         |
| import | pkg         |

Влияет на относительные импорты.

---

## 7. Главное правило архитектуры

Для пакетных проектов:

* использовать пакеты
* запускать через `-m`
* не запускать файлы внутри пакета напрямую
* использовать `if __name__ == "__main__"`

---

## 8. Ключевая модель

| режим             | **name** | **package** | sys.path[0]  |
| ----------------- | -------- | ----------- | ------------ |
| python file.py    | **main** | None        | dir(file)    |
| python -m pkg.mod | **main** | pkg         | project root |
| import pkg.mod    | pkg.mod  | pkg         | unchanged    |

Это основа import / execution в Python.
