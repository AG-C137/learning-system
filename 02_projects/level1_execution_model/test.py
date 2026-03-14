import sys

print("STEP 1")

print("__name__ =", __name__)
print("__package__ =", __package__)

print("in sys.modules =", __name__ in sys.modules)

print("module object =", sys.modules[__name__])

print("STEP 2")