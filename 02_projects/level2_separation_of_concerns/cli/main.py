print("cli loaded")

from services.user_service import process_user


def start():
    text = process_user()
    print(text)