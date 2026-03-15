import sys
from pprint import pprint

print("EXECUTABLE:", sys.executable)
print("FILE:", __file__)
print("NAME:", __name__)
print("PACKAGE:", __package__)

print("\nSYS.PATH:")
pprint(sys.path)
