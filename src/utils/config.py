import logging
import os
from datetime import datetime
from pathlib import Path

# --- CONFIGURACIÓN DE RUTAS ---
# Suponiendo que este archivo está en src/utils/config.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# --- CONFIGURACIÓN DE GLOBALES ---
# Aquí puedes mover las constantes que tenías en globals.py
REGION_MS_WINDOW = (0, 0, 800, 600) 
REGION_TOTAL_MINUS_MS_WINDOW = (800, 0, 1120, 1080)
POSITIONS_FIELDS = []
POSITIONS_MOUSE_6_TURNS = []
mode = "default"
stop_loop = False
accounts = ["acc1", "acc2"]
accounts2 = {"acc1": "123", "acc2": "456"}

# --- CONFIGURACIÓN DE LOGGING ---
def setup_logging(script_name: str):
    # Limpiamos handlers previos si existen
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    log_file = LOG_DIR / f"{script_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    
    # Formato para el archivo (detallado)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
    )
    
    # Formato para la consola (resumido)
    console_formatter = logging.Formatter("%(message)s")

    # Handler para el archivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Handler para la consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO) # Solo INFO o superior a consola

    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_file
