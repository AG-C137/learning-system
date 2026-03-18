print("greet_user loaded")

from core.user_logic import build_user_text
from config.settings import USER_NAME


def greet_user():
    return build_user_text(USER_NAME)