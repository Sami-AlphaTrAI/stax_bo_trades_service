import logging
import os

def setup_logging():
    LOG_PATH = os.environ.get("LOG_PATH", "app.log")
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    