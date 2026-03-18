print("core loaded")

from config.settings import VALUE
from cli.main import start   # ❌ запрещено

def do_logic():
    print("logic", VALUE)