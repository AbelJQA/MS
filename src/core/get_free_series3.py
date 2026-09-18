from src.utils.globals import *
from src.utils.my_functions import *
import src.utils.my_functions as my_functions
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



first_time_login = True

globals.set_mode('normal_6t')

try:
    logger.info("Execution started")

    pg.moveTo(1500, 100)
    logger.info("Mouse moved to initial position")

    subprocess.run(
        ["taskkill", "/im", "snap.exe", "/f"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("snap.exe terminated if it was running")

    start_obs_then_record()
    logger.info("OBS started and recording")

    resize_window_by_tuple(
        title_contains=["py", "eight_hours"],
        region=globals.REGION_TOTAL_MINUS_MS_WINDOW,
    )
    logger.info("Console window resized")

    if globals.first_time_login:
        close_steam_windows()
        logger.info("Steam popup windows closed")

    for account in globals.accounts:
        logger.info("Processing account: %s", account)

        os.startfile("steam://rungameid/1997040")
        logger.info("Game relaunched for account")
        
        
        resize_window_by_tuple(
            ["SNAP"],
            region=globals.REGION_MS_WINDOW,
        )
        logger.info("Game window resized")
        
        
        login(account)
        logger.info("Login executed")

        search_initial_imgs()
        logger.info("Initial images processed")

        os.system("taskkill /im chrome.exe /f")
        logger.info("Chrome terminated")

        # Entrando a la tienda para reclamar tokens gratis
        click_any_MS_img(r'images/unselected/shop_unselected.PNG')
        click_any_MS_img(r'images/stages/shop/cards_shop.PNG')
        click_any_MS_img(r'images/free_series3.PNG')
        time.sleep(3)
        if click_any_MS_img(r'images/claim_series3.PNG', timeout=0):
            click_any_MS_img(r'images/claim_series3_step2.PNG')

            if search_MS_img(r'images/claim_series3_step3.png', timeout=3):
                time.sleep(3)
                click_any_MS_img(r'images/claim_series3_step3.png')
                time.sleep(1)
                
        presionar_esc()
        
        logout()

    beep_forever()
    #end_record_obs()
    # To shut down immediately
    #os.system("shutdown /s /t 0")

except Exception as e:
    print(e)