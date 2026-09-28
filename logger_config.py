import logging
import os
import sys
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

script_name = os.path.splitext(os.path.basename(__file__))[0]
LOG_FILE = LOG_DIR / f"{script_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"


logging.basicConfig(
    force=True,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.__stdout__),
    ],
)

logger = logging.getLogger(__name__)


class StreamToLogger:
    def __init__(self, logger, level, original_stream):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream

    def write(self, message):
        if message.strip():
            self.logger.log(self.level, message.strip())
            self.original_stream.write(message)
            self.original_stream.flush()

    def flush(self):
        self.original_stream.flush()


sys.stdout = StreamToLogger(logger, logging.INFO, sys.__stdout__)
sys.stderr = StreamToLogger(logger, logging.ERROR, sys.__stderr__)


def global_exception_handler(exc_type, exc_value, exc_traceback):
    logger.exception(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = global_exception_handler