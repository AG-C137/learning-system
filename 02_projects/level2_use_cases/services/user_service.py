print("service loaded")

from config.settings import DEFAULT_NAME, PREFIX
from core.user_logic import build_greeting


def greet_user():
    name = DEFAULT_NAME
    return build_greeting(PREFIX, name)


def greet_custom(name: str):
    return build_greeting(PREFIX, name)