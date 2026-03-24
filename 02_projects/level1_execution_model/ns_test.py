x = 10

def f():
    pass

import sys

mod = sys.modules[__name__]

print("globals is dict:", isinstance(globals(), dict))
print("globals == mod.__dict__:", globals() is mod.__dict__)