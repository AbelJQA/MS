import time
import os
import logging
import pyautogui as pg
import subprocess
import pygetwindow as gw
from src.utils import globals
from src.utils.image_processing import *
from src.utils.json_helpers import *
from src.utils.my_functions import resize_window_by_tuple
from src.utils.obs_helpers import *

logger = logging.getLogger(__name__)

# --- IMPORTACIONES DINÁMICAS PARA EVITAR CICLOS ---
def _get_my_functions():
    from src.utils import my_functions
    return my_functions

def login(acc):
    account_img = rf'images/accounts/relogin_accounts/gmail_accounts/vm/{acc}.png'
    if not os.path.exists(account_img):
        _get_my_functions().beep_forever()
        raise FileNotFoundError(f"Account image not found: {account_img}")
    
    os.startfile("steam://rungameid/1997040")
    logger.info("[DEBUG] Resizing SNAP window...")
    resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, timeout=5)
    
    if click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2, timeout=90):
        pass
    else:
        # Nota: Aquí se asume que search_initial_imgs estará disponible o se moverá también
        logout()
        login(acc)
        return

    time.sleep(2)
    click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2)
    
    resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, timeout=1)
    
    if search_MS_img(r'images/please_sign.png', alert_on_fail=False):
        click_any_MS_img(r'images/ok_btn.png')
        # ... (simplificado para la migración)
        
    click_any_MS_img(r'images/stages/main_stage/sign_in_with_google2.PNG')
        
    if search_MS_img(r'images/pagina_cargada.png', timeout=60):
        try:
            chrome_window = gw.getWindowsWithTitle('Google Chrome')[0]
            chrome_window.maximize()
        except IndexError:
            pass
        time.sleep(2)
        if not click_any_MS_img(account_img, region=(0,0,1920,900), delay_click=3, timeout=0):
            start_time = time.time()
            while time.time() - start_time < 5:
                pg.moveTo(500, 500)  
                pg.scroll(-500)
                time.sleep(0.5)
                if click_any_MS_img(account_img, region=None, delay_click=3, timeout=0):
                    break
    
    if search_MS_img(r'images/marvelsnap_web.png', timeout=30, confidence=.7):
        os.system("taskkill /im chrome.exe /f")

def logout():
    click_any_MS_img(r'images/stages/main_stage/nut.png')
    click_any_MS_img(r'images/graphics_quality.png', timeout=3)
    time.sleep(1)
    pg.scroll(-800)
    click_any_MS_img(r'images/stages/main_stage/sign_out.png')
    time.sleep(1)
    click_any_MS_img(r'images/sign_out_grande.png')
    click_any_MS_img(r'images/stages/main_stage/sign_out2.png')
    time.sleep(1)
    click_any_MS_img(r'images/stages/main_stage/sign_out2_hover.png')
    resize_window_by_tuple("SNAP", region=globals.REGION_MS_WINDOW, timeout=2)
    time.sleep(1)
    os.system("taskkill /im snap.exe /f")
    time.sleep(3)

def upgrade_cards(cards_to_upgrade):
    logger.info("[INFO] Iniciando mejora de cartas")
    if not click_any_MS_img([r'images/stages/shop/upgrade_cards_icon.PNG', r'images/stages/shop/upgrade_cards_icon_selected.PNG'], timeout=3):
        return

    time.sleep(1)
    cartas_a_mejorar = cards_to_upgrade
    i = 0
    while i < cartas_a_mejorar:
        pg.click(218 + 150 * i, 580)
        time.sleep(1)
        pg.click(374, 889)
        time.sleep(7)
        pg.click(374, 889)
        
        if search_MS_img("images/aw_snap.png", timeout=3):
            click_any_MS_img("images/x.png")
            # ... navegación para reset ...
            i = 0
            continue
        
        if click_any_MS_img(r'images/you_need_more_credits!.png', timeout=3):
            _get_my_functions().presionar_esc(2)
            time.sleep(2)
            break
        else:
            time.sleep(5)
            pg.click(374, 889)
            time.sleep(5)
            _get_my_functions().presionar_esc()
            time.sleep(1)
        i += 1
    logger.info("[INFO] Mejora de cartas completada ✅")
