# process_probe.py
import os
import sys

print("PID:", os.getpid())
print("Executable:", sys.executable)
print("Arguments:", sys.argv)