print("service loaded")

from config.settings import DEFAULT_NAME, PREFIX
from core.user_logic import build_greeting


def process_user():
    name = DEFAULT_NAME

    text = build_greeting(PREFIX, name)

    return text