from src.utils.globals import *
from src.utils.my_functions import *

import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# CONFIG
# ============================================================

ITERATIONS = 32

# ============================================================
# LOGGING
# ============================================================

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

script_name = os.path.splitext(os.path.basename(__file__))[0]

LOG_FILE = LOG_DIR / f"{script_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

logging.basicConfig(
    force=True,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.__stdout__),
    ],
)

logger = logging.getLogger(__name__)
logger.info("Logger initialized")

# ============================================================
# INIT
# ============================================================

resize_window_by_tuple(
    ["SNAP"],
    region=globals.REGION_MS_WINDOW,
)

logger.info("Window resized")

# ============================================================
# MAIN LOOP
# ============================================================

for i in range(ITERATIONS):

    time.sleep(1)

    # visual comment: SHOP
    shop_pos = search_MS_img("images/shop.png", timeout=5)
    if not shop_pos:
        logger.info("[SHOP] Not found")
        continue

    logger.info("[SHOP] Found")

    time.sleep(1)

    # visual comment: click offset
    click_pos((shop_pos.x - 100, shop_pos.y))
    logger.info("[ACTION] Click shop offset")

    time.sleep(1)

    # visual comment: QUESTION MARK
    q_pos = search_MS_img("images/question_mark.png", timeout=5)
    if q_pos:
        click_pos((q_pos.x, q_pos.y))
        logger.info("[ACTION] Question mark")

    time.sleep(1)

    # visual comment: FORFEIT 1
    f1 = search_MS_img("images/forfeit.png", timeout=5)
    if f1:
        click_pos((f1.x, f1.y))
        logger.info("[ACTION] Forfeit 1")

    time.sleep(1)

    # visual comment: FORFEIT 2
    f2 = search_MS_img("images/forfeit.png", timeout=5)
    if f2:
        click_pos((f2.x, f2.y))
        logger.info("[ACTION] Forfeit 2")

    logger.info(f"[LOOP] Iteration {i + 1}")
    
beep_forever()