from .service import process

def run_cli():
    print("CLI started")
    result = process("hello")
    print(result)