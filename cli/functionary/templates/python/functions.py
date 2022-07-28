import logging


def hello():
    print("Hello Docker World")


def echo(message="Hello Docker", loud=False):
    logging.getLogger(__name__).info(f"Creating message, loud:{loud}")

    return f"{message}{'!!!!!!!!!' if loud else ''}"
