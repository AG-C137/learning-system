Главное понимание

Circular import ломается не потому что Python глупый.

А потому что:

module кладётся в sys.modules
до завершения выполнения

Это нужно, чтобы import вообще мог работать.

Но это создаёт:

partial module

incomplete state

ошибки

10. Что ты должен вынести из Level1

✔ import = cache
✔ cache = sys.modules
✔ module создаётся до выполнения
✔ circular import = incomplete module
✔ поэтому ошибки