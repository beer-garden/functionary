import logging
import os

from runner.listener import start_listening
from runner.messaging import wait_for_connection

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)


if __name__ == "__main__":
    wait_for_connection()
    start_listening()
