from globals import *
from my_functions import *
import my_functions

import logging
import os
from datetime import datetime
import sys
import signal

# ============================================================
# BASIC LOGGING CONFIGURATION
# ============================================================

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Nombre del script
script_name = os.path.splitext(os.path.basename(__file__))[0]

LOG_FILE = LOG_DIR / (
    f"{script_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

# Forzar creación inmediata del archivo
LOG_FILE.touch()  # ← agrega esta línea

# Handler con flush inmediato
_file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# Subclase simple que hace flush después de cada línea
class _ImmediateFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.stream.flush()

logging.basicConfig(
    force=True,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        _ImmediateFileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.__stdout__),
    ],
)

logger = logging.getLogger(__name__)
logger.info("LOG FILE PATH: %s", LOG_FILE)
logger.info("Logger initialized")

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

# visual comment: capture any uncaught exception and log it
def global_exception_handler(exc_type, exc_value, exc_traceback):
    logger.exception(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
    )

sys.excepthook = global_exception_handler

logger.info("TEST LOG INITIALIZATION")
logger.info("Logger test executed")

# visual comment: handle Ctrl+C and forced exits
def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received. Stopping OBS recording...")
    try:
        end_record_obs()
    except Exception as e:
        logger.error(f"Error stopping OBS: {e}")
    finally:
        sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler)  # kill / cierre externo


######### MAIN

pg.click()
