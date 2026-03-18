print("greet_user loaded")

from app.core.user_logic import build_user_text
from app.config.settings import USER_NAME # type: ignore


def greet_user():
    return build_user_text(USER_NAME)