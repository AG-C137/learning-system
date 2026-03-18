print("cli loaded")

from app.services.user.greet_user import greet_user
from app.services.user.greet_custom import greet_custom


def start():
    text1 = greet_user()
    print(text1)

    text2 = greet_custom("Bob")
    print(text2)

if __name__ == "__main__":
    start()