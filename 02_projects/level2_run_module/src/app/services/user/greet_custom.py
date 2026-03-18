print("greet_custom loaded")

from app.core.user_logic import build_user_text


def greet_custom(name):
    return build_user_text(name)