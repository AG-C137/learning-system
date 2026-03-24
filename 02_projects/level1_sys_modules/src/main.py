import sys
import pkg.mod

print("pkg in cache:", "pkg" in sys.modules)
print("pkg.mod in cache:", "pkg.mod" in sys.modules)