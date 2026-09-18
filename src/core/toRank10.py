from src.utils.globals import *
from src.utils.my_functions import *
from src.utils import my_functions

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



resize_window_by_tuple(
    title_contains=["toRank10"],  # nombre de tu terminal/script
    region=globals.REGION_TOTAL_MINUS_MS_WINDOW,
)
logger.info("Console window resized")

start_obs_then_record()
logger.info("OBS started and recording")

resize_window_by_tuple(['SNAP'], globals.REGION_MS_WINDOW, delay=10)
logger.info("Game window resized")


while not check_rank_reached():
    
    if click_any_MS_img(
            "images/stages/play_stage/play.PNG",
            delay_click=3,
        ):
        logger.info("Play button clicked")

        while not search_MS_img(
            "images/stages/play_stage/collect_rewards.PNG",
            quick_check=True,
        ):
            end_turn = search_MS_img(
                "images/stages/play_stage/end_turn.PNG",
                quick_check=True,
            )

            if end_turn:
                click_any_MS_img(
                    "images/stages/play_stage/snap.PNG",
                    quick_check=True,
                    timeout=0,
                )
                play_cards_ahk(
                    globals.POSITIONS_MOUSE_6_TURNS
                )
                click_pos(end_turn)
                logger.info("End turn executed")

            never = search_MS_img(
                "images/stages/play_stage/never_seen_before.png",
                quick_check=True,
                timeout=0,
            )

            if never:
                pg.moveTo(never)
                pg.move(0, 300)
                time.sleep(0.3)
                pg.click()
                logger.warning("Unknown popup handled")

            if search_MS_img(
                "images/aw_snap.png",
                timeout=0,
                quick_check=True,
            ):
                time.sleep(2)
                presionar_esc()
                logger.warning("aw_snap detected")

            if search_MS_img(
                rf"C:\Users\{os.getlogin()}\OneDrive\my_py_projects\MS\images\stages\play_stage\flechas.png",
                timeout=0,
                quick_check=True,
            ):
                time.sleep(2)
                presionar_esc()
                click_any_MS_img(
                    "images/stages/play_stage/end_turn.PNG",
                    quick_check=True,
                    timeout=0,
                )
                logger.warning("Arrow overlay handled")

        logger.info("Rewards detected, exiting match")

        click_any_MS_img(
            "images/stages/play_stage/collect_rewards.PNG"
        )
        click_any_MS_img(
            "images/stages/play_stage/next.PNG"
        )

    time.sleep(2)
    
beep_forever()