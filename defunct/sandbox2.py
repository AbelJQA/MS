import csv
import sys

import pandas as pd

from globals import *
from my_functions import *
import my_functions

import logging
import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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


logging.basicConfig(
    force=True,
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(filename)s:%(lineno)d | %(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
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

# ============================================================
# ANTI-SPAM LOGGER
# ============================================================

last_log = {}

def log_once(key, message, interval=5, level=logging.INFO):
    now = time.time()

    if now - last_log.get(key, 0) >= interval:
        logger.log(level, message)
        last_log[key] = now



    
##### MAINNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNNN

try:
    start_obs_then_record()
    pg.moveTo(1500, 100)
    os.system("taskkill /im snap.exe /f")
    logger.info("snap.exe terminated if it was running")
    resize_window_by_tuple(title_contains=["py", "eight_hours"], region=globals.REGION_TOTAL_MINUS_MS_WINDOW)
    # if not is_steam_running():
    #     time.sleep(30)
    #     close_steam_windows()    
    
    # --- Archivo CSV de salida ---
    archivo_salida = "cartas_cuentas.csv"

    with open(archivo_salida, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Escribir encabezados básicos
        writer.writerow(["Cuenta", "Total Cartas", "Lista de Cartas"])

        for account in globals.accounts:
            logger.info("Processing account: %s", account)
            os.startfile("steam://rungameid/1997040")
            resize_window_by_tuple(["SNAP"],region=globals.REGION_MS_WINDOW)
            login(account)
            search_initial_imgs()
            
            click_any_MS_img(r'images/start_screen/maybe_later.PNG', timeout=2)
            click_any_MS_img(r'images/start_screen/maybe_later2.PNG', timeout=0.01)
            click_pos((232, 968))
            time.sleep(5)
            update_json_info('CollectionState')
            
            lista_cartas = procesar_cartas_cuenta(account)
            if lista_cartas:
                cartas_juntas = ", ".join(lista_cartas)
                # Guardar la fila directamente
                writer.writerow([account, len(lista_cartas), cartas_juntas])

            presionar_esc()
            logout()


    #beep_forever()
    end_record_obs()
    logger.info("OBS recording stopped")


except Exception as e:
    logger.exception("Unhandled exception occurred")

    input("\nPresiona ENTER para cerrar...")