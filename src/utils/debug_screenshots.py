import os
import pyautogui as pg
from datetime import datetime
from pathlib import Path
from src.utils import globals

DEBUG_DIR = Path("debug_screenshots")


def debug_screenshot(nombre, region=globals.REGION_MS_WINDOW):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    archivo = DEBUG_DIR / f"{timestamp}_{nombre}.png"

    screenshot = pg.screenshot(region=region)
    screenshot.save(archivo)

    return archivo