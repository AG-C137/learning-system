print("service loaded")

from core.user_logic import build_greeting
from config.settings import DEFAULT_NAME


def process_user():
    name = DEFAULT_NAME
    text = build_greeting(name)
    return text