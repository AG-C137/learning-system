print("cli main loaded")

from app.core.greet import greet


def main():
    print(greet("Alex"))


if __name__ == "__main__":
    main()