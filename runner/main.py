import logging
import os

from runner.listener import start_listening

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(level=LOG_LEVEL)

if __name__ == "__main__":
    start_listening()
