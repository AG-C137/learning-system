import sys

print("name:", __name__)
print("package:", __package__)
print("file:", __file__)

print("in sys.modules:", __name__ in sys.modules)