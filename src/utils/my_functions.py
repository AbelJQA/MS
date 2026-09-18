import logging
logger = logging.getLogger(__name__)

import socket
import json
import subprocess
from datetime import datetime
from datetime import time as tm
import os
import pyautogui as pg
import time
import keyboard
import pygetwindow as gw
import winsound
import psutil
import shutil
import cv2
import numpy as np
import easyocr

# from src.utils.obs_helpers import *
# from src.utils.json_helpers import *
# from src.utils.image_processing import *
# from src.utils.game_logic import *
from src.utils import globals

def click_pos(pos, delay_click=1):
    if pos is None:
        logger.info("click_pos recibió None, no se hace clic")
        return
    x, y = pos
    logger.info(f"Haciendo click en la posición ({x}, {y})")
    pg.moveTo(x, y)
    time.sleep(delay_click)
    pg.click(x, y)

def presionar_esc(veces=1):
    for i in range(veces):
        logger.info(f"Presionando ESC ({i+1}/{veces})")
        time.sleep(0.2)
        keyboard.press('\x1b')
        time.sleep(0.1)
        keyboard.release('\x1b')
        time.sleep(0.3)

def beep_forever():
    while True:
        winsound.Beep(500, 500)
        time.sleep(10)


def search_MS_img(
        path,
        timeout=0,
        confidence=0.8,
        region=globals.REGION_MS_WINDOW,
        interval_searching=0,
        quick_check=False,
        alert_on_fail=False,
        verbose=True
):

    start_time = time.time()

    if not quick_check and verbose:
        logger.info(
            f"Searching {os.path.basename(path)} (timeout={timeout}s)"
        )

    while True:

        elapsed = time.time() - start_time

        try:
            position = pg.locateCenterOnScreen(
                path,
                confidence=confidence,
                region=region,
            )
        except Exception as e:
            if verbose:
                logger.info(
                    f"[ERROR] Exception while searching "
                    f"{os.path.basename(path)} -> {e}"
                )

            if alert_on_fail:
                beep_forever()

            return None

        if position:
            total_time = round(time.time() - start_time, 2)

            if verbose:
                logger.info(
                    f"\n✅ Found: {os.path.basename(path)} "
                    f"pos=({int(position[0])}, {int(position[1])}) "
                    f"time={total_time}s confidence={confidence}"
                )

            return position

        if quick_check:
            return None

        if elapsed > timeout:

            if verbose:
                logger.info(
                    f"\n⛔ Not found: {os.path.basename(path)} "
                    f"after {round(elapsed, 2)}s "
                    f"region={region} confidence={confidence}"
                )

            if alert_on_fail:
                beep_forever()

            return None

        time.sleep(interval_searching)


def click_any_MS_img(
    paths, 
    timeout=20, 
    delay_click=1, 
    region=globals.REGION_MS_WINDOW, 
    confidence=0.8, 
    **kwargs
):
    """
    Busca una o varias imágenes al mismo tiempo.
    Evita conflictos si se pasan 'quick_check' o 'timeout' por kwargs.
    """
    if isinstance(paths, str):
        paths = [paths]

    # 🌟 CORRECCIÓN: Limpiamos kwargs para que no duplique parámetros en search_MS_img
    kwargs.pop('quick_check', None)
    kwargs.pop('timeout', None)

    start_time = time.time()
    
    logger.info(
        f"[DEBUG] Buscando en paralelo: {[os.path.basename(p) for p in paths]} "
        f"| timeout={timeout}s | confidence={confidence}"
    )

    while True:
        for path in paths:
            # Ahora ya no fallará aunque invoques la función con quick_check=True fuera
            position = search_MS_img(
                path,
                timeout=0, # Forzado a 0 para que sea inmediato en el bucle
                region=region,
                confidence=confidence,
                quick_check=True, # Forzado a True para que no se quede trabado
                verbose=False,
                **kwargs,
            )

            if position:
                time.sleep(delay_click)
                click_pos(position, delay_click=0)

                logger.info(
                    f"🖱️ Click OK (En paralelo): {os.path.basename(path)} "
                    f"at ({int(position[0])}, {int(position[1])}) "
                    f"delay={delay_click}s"
                )
                time.sleep(1)
                pg.moveTo(1,500)  
                return True

        # Si el timeout original que pasaste era 0, o si ya pasó el tiempo, sale.
        elapsed = time.time() - start_time
        if timeout == 0 or elapsed > timeout:
            logger.info(
                f"[DEBUG] Click skipped, ninguna de las imágenes se encontró "
                f"en el intento."
            )
            time.sleep(1)
            pg.moveTo(0,500)  
            return False
        
        time.sleep(0.1)



# Asumo que 'reader' ya está inicializado en tu script globalmente:
# Variable global interna (empieza vacía para no ralentizar el 'import')
_reader = None

def _get_reader():
    """Inicializa el lector de EasyOCR solo cuando es estrictamente necesario."""
    global _reader
    if _reader is None:
        # Aquí puedes meter un log si quieres saber exactamente cuándo se despierta
        # logger.info("Inicializando el modelo de EasyOCR por primera vez...")
        _reader = easyocr.Reader(['es'])
    return _reader


def search_MS_text_ocr(
        path_or_text,  # Ahora acepta el texto a buscar en lugar de una ruta de imagen
        timeout=0,
        confidence=0.35, # Equivalente al text_threshold / umbral_minimo
        region=globals.REGION_MS_WINDOW,
        interval_searching=0,
        quick_check=False,
        alert_on_fail=False,
        verbose=True
):
    start_time = time.time()
    palabra_buscar_clean = str(path_or_text).strip().upper()

    if not quick_check and verbose:
        logger.info(
            f"Searching text '{path_or_text}' (timeout={timeout}s)"
        )

    screenshot = None

    # Llamamos al cargador inteligente de EasyOCR justo antes del bucle
    reader = _get_reader()

    while True:
        elapsed = time.time() - start_time
        position = None

        try:
            # 1. Tomar captura de la región para procesar con EasyOCR
            screenshot = pg.screenshot(region=region)
            image_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 2. Procesar con EasyOCR usando el confidence como umbral mínimo
            results = reader.readtext(image_cv, paragraph=False, text_threshold=confidence)

            for bbox, text, prob in results:
                text_clean = text.strip().upper()

                # Verificar coincidencia de texto y umbral de confianza
                if palabra_buscar_clean in text_clean and prob >= confidence:
                    puntos_en_pantalla = [tuple(map(int, p)) for p in bbox]
                    top_left = puntos_en_pantalla[0]
                    bottom_right = puntos_en_pantalla[2]

                    # Calcular centro LOCAL
                    centro_x = int((top_left[0] + bottom_right[0]) / 2)
                    centro_y = int((top_left[1] + bottom_right[1]) / 2)

                    # =========================================================
                    # LÓGICA DE GUARDADO EN CASO DE ÉXITO
                    # =========================================================
                    carpeta_exito = "exito_ocr"
                    if not os.path.exists(carpeta_exito):
                        os.makedirs(carpeta_exito)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    palabra_segura = "".join([c for c in str(path_or_text) if c.isalpha() or c.isdigit()]).rstrip()
                    nombre_archivo_exito = f"{carpeta_exito}/exito_{palabra_segura}_{timestamp}.png"

                    cv2.rectangle(image_cv, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.imwrite(nombre_archivo_exito, image_cv)

                    # Ajustar coordenadas LOCALES a GLOBALES si hay una región activa
                    if region:
                        centro_x += region[0]
                        centro_y += region[1]

                    position = (centro_x, centro_y)
                    break # Salimos del for al encontrar la primera coincidencia válida

        except Exception as e:
            if verbose:
                logger.info(
                    f"[ERROR] Exception while searching text "
                    f"'{path_or_text}' -> {e}"
                )
            if alert_on_fail:
                beep_forever()
            return None

        # Si se encontró la posición, registrar logs y retornar
        if position:
            total_time = round(time.time() - start_time, 2)
            if verbose:
                logger.info(
                    f"\n✅ Found text: '{path_or_text}' "
                    f"pos=({int(position[0])}, {int(position[1])}) "
                    f"time={total_time}s confidence={confidence}"
                )
            return position

        if quick_check:
            return None

        # Verificar si excedió el timeout general
        if elapsed > timeout:
            if verbose:
                logger.info(
                    f"\n⛔ Text not found: '{path_or_text}' "
                    f"after {round(elapsed, 2)}s "
                    f"region={region} confidence={confidence}"
                )

            # =========================================================
            # LÓGICA DE GUARDADO EN CASO DE ERROR (TIMEOUT EXCEDIDO)
            # =========================================================
            if screenshot is not None:
                carpeta_errores = "errores_ocr"
                if not os.path.exists(carpeta_errores):
                    os.makedirs(carpeta_errores)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                palabra_segura = "".join([c for c in str(path_or_text) if c.isalpha() or c.isdigit()]).rstrip()
                nombre_archivo_error = f"{carpeta_errores}/error_{palabra_segura}_{timestamp}.png"
                screenshot.save(nombre_archivo_error)

            if alert_on_fail:
                beep_forever()

            return None

        # Control del delay de escaneo (interval_searching) configurado en tu función original
        time.sleep(interval_searching if interval_searching > 0 else 0.1)


def click_any_MS_text_ocr(
    paths, # Ahora representará una lista de textos a buscar en paralelo
    timeout=20, 
    delay_click=1, 
    region=globals.REGION_MS_WINDOW, 
    confidence=0.35, 
    **kwargs
):
    """
    Busca una o varias palabras al mismo tiempo en la pantalla.
    Evita conflictos si se pasan 'quick_check' o 'timeout' por kwargs.
    """
    if isinstance(paths, str):
        paths = [paths]

    kwargs.pop('quick_check', None)
    kwargs.pop('timeout', None)

    start_time = time.time()
    
    logger.info(
        f"[DEBUG] Buscando texto en paralelo: {paths} "
        f"| timeout={timeout}s | confidence={confidence}"
    )

    while True:
        for path in paths:
            # CORRECCIÓN: Aquí llamabas a search_MS_img, cambiada a search_MS_text_ocr
            position = search_MS_text_ocr(
                path,
                timeout=0, 
                region=region,
                confidence=confidence,
                quick_check=True, 
                verbose=False,
                **kwargs,
            )

            if position:
                time.sleep(delay_click)
                click_pos(position, delay_click=0)

                logger.info(
                    f"🖱️ Click OK (Texto en paralelo): '{path}' "
                    f"at ({int(position[0])}, {int(position[1])}) "
                    f"delay={delay_click}s"
                )
                time.sleep(1)
                pg.moveTo(1,1)  
                return True

        elapsed = time.time() - start_time
        if timeout == 0 or elapsed > timeout:
            logger.info(
                f"[DEBUG] Click skipped, ninguno de los textos se encontró "
                f"en el intento."
            )
            time.sleep(1)
            pg.moveTo(0,500)  
            return False
        
        time.sleep(0.1)




def get_nvprod_json_path(json_filename):
    return (
        rf"C:\Users\{os.getlogin()}\AppData\LocalLow\Second Dinner"
        rf"\SNAP\Standalone\States\nvprod\{json_filename}.json"
    )


def update_json_info(json_filename):
    ruta_archivo = get_nvprod_json_path(json_filename)
    subprocess.Popen(["notepad.exe", ruta_archivo])
    time.sleep(2)
    subprocess.run(['taskkill', '/F', '/IM', 'notepad.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# Conquest
def get_postgame_xp_value():
    with open(get_nvprod_json_path("BattlePassState"), "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return (
        data.get("ServerState", {})
            .get("BattlePass", {})
            .get("PostGameXpTrackedAmount", 0)
    )
#



def count_available_submissions():
    file_path = get_nvprod_json_path('MissionState')

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    daily_group = data['ServerState']['State']['DailyMissionGroup']
    submissions = daily_group.get('SubMissions', [])

    available = min(len(submissions), 6)
    logger.info("AVAILABLE: %s", available)
    
    return available



def check_at_least_n_submissions_complete(required_missions):
    file_path=get_nvprod_json_path('MissionState')
    
    """Verifica si hay al menos N misiones completas."""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
        daily_group = data['ServerState']['State']['DailyMissionGroup']
        submissions = daily_group.get('SubMissions', [])

    completed = 0
    for sub in submissions:
        required = sub.get('RequiredProgress')
        current = sub.get('CurrentProgress')
        if required is not None and current is not None and required == current:
            completed += 1

    logger.info(f"Misiones completadas: {completed}")

    return completed >= required_missions



def extract_value_from_json(file_path, key_path):
    """
    file_path: string con la ruta al archivo JSON
    key_path: lista de llaves en orden, por ejemplo:
              ['ServerState', 'CollectionScore', 'Amount']
    """
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    current = data
    for key in key_path:
        current = current[key]

    return current




def get_CL_from_json():
    
    update_json_info('CollectionState')

    with open(get_nvprod_json_path('CollectionState'), 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    daily_group = data['ServerState']['CollectionScore']['Amount']
    logger.info(daily_group)

    return daily_group



def get_completed_missions():
    '''Devuelve la cantidad de misiones completadas'''    
    with open(get_nvprod_json_path('MissionState'), 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    daily_group = data['ServerState']['State']['DailyMissionGroup']
    submissions = daily_group.get('SubMissions', [])

    count_equal = 0

    for m in submissions:
        current = m.get("CurrentProgress", 0)
        required = m.get("RequiredProgress", 0)

        if current == required:
            count_equal += 1

    return count_equal


def check_rank_reached(target_rank=10):
    file_path = get_nvprod_json_path('ProfileState')

    rank = extract_value_from_json(
        file_path,
        ['ServerState', 'RankLog', 'Rank']
    )

    print(f"Rank actual: {rank}")
    logger.info(f"Current rank: {rank}")

    if rank >= target_rank:
        logger.info("Rank objetivo alcanzado")
        beep_forever()
        return True

    return False



def has_snap_account(retries=5, delay=2):
    """Try to read AccountState JSON several times until SnapAccount is found."""
    file_path = get_nvprod_json_path('AccountState')

    for _ in range(retries):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        server_state = data.get('ServerState', {})
        partner_account = server_state.get('PartnerAccount')

        if partner_account and partner_account.get('SnapAccountId'):
            snap_id = partner_account['SnapAccountId']
            logger.info(f"Snap Account detected: {snap_id}")
            return True

        time.sleep(delay)

    logger.info("No Snap Account found")
    return False


def reclamar_25creditos_gratis():
    # Entrando a la tienda para reclamar 25 credits

    click_any_MS_img(["images/stages/shop/offers.PNG", "images/offers_selected.PNG"])
    click_any_MS_img(["images/credits_selected.png", "images/stages/shop/credits.PNG"], timeout=3)
    time.sleep(1.5)
    click_any_MS_img("images/claim_25_credits.png", timeout=3)
    if search_MS_img("images/aw_snap.png", timeout=3):
        click_any_MS_img("images/x.png")


def after_finish_all_games():
    if globals.mode == "sanctum":
        presionar_esc()

    # Chequeando las misiones y recoger las recompensas
    click_any_MS_img(
        r'images/stages/main_stage/missionsNotify2.png',
        delay_click=3
    )
    click_blue_missions_2()
    get_weekly_rewards()

    # Entrando a la tienda para reclamar tokens y creditos gratis

    click_pos((557, 64))  # Position of gold icon
    click_any_MS_img(r'images/stages/shop/cards_shop.PNG')
    click_any_MS_img(r'images/stages/shop/token_icon.PNG')
    time.sleep(2)
    click_any_MS_img(r'images/stages/shop/claim!_token_3.PNG', timeout=4)
    # reclamar_25creditos_gratis()
        
    # Entrando a la tienda para levear cartas
    
    click_any_MS_img(r'images/stages/shop/cards_shop.PNG')
    click_any_MS_img(r'images/stages/shop/offers.PNG')
    upgrade_cards(3)
    presionar_esc() # Saliendo al menu principal
    click_any_MS_img("images/start_screen/offer_window/white_x.png", timeout=2)


def get_current_account_name():
    path = rf"C:\Users\{os.getlogin()}\AppData\LocalLow\Second Dinner\SNAP\Standalone\States\nvprod\AccountState.json"
    
    with open(path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    
    current_id = data["ServerState"]["Account"]["Id"]
    
    for name, acc_id in globals.accounts2.items():
        if acc_id == current_id:
            return name
    
    return "Desconocido"


def confirm_initial_images_passed():
    time.sleep(8)
    if search_MS_img(r'images/unselected/shop_unselected.PNG', timeout=0):
        logger.info('Ya esta listo')
        return True
    return False


def search_initial_imgs():

    # Buscando imagenes que aparecen siempre al inicio del juego
    start_time = time.time()
    while time.time() - start_time < 90:

        if search_MS_img(r'images/unselected/shop_unselected.PNG', timeout=0):
            if confirm_initial_images_passed():
                break

        elif click_any_MS_img(
            r'images/super_premium.PNG', timeout=0
        ):
            presionar_esc()
            if confirm_initial_images_passed():
                break
        
        elif click_any_MS_img(
            r'images/start_screen/maybe_later.PNG', timeout=0
        ):
            if confirm_initial_images_passed():
                break

        elif click_any_MS_img(r'images/start_screen/maybe_later2.PNG', timeout=0):
            if confirm_initial_images_passed():
                break

        elif search_MS_img(r'images/start_screen/go_to_shop.PNG', timeout=0):
            time.sleep(2)
            click_any_MS_img(r'images/start_screen/offer_window/white_x.png')
            if confirm_initial_images_passed():
                break

        # Cambiar name de la imagen segun el evento
        elif click_any_MS_img(
            r'images/start_screen/14_days_of_winterverse.PNG',
            timeout=0
        ):
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)

            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 15:
                    for img in images:
                        click_any_MS_img(img, timeout=0)

            # Moviendo puntero
            pg.moveTo(10, 10)

            if confirm_initial_images_passed():
                break

        elif search_MS_img(
            r'images/start_screen/welcome_back_calendar.PNG',
            timeout=0
        ):
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)

            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 15:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            elif claim := search_MS_img(r'images/claim_hover.png', timeout=3):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 15:
                    for img in images:
                        click_any_MS_img(img, timeout=0)

            # Moviendo puntero
            pg.moveTo(10, 10)

            if confirm_initial_images_passed():
                break
        
        elif click_any_MS_img(
            r'images/start_screen/start_the_countdown.PNG', timeout=0
        ):
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)

            '''
            if claim := wait_for_image(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)
                wait_for_image_and_click(r'images/stages/collection_rewards_stage/nice!.PNG', timeout=5)
            '''

            start2 = time.time()
            while time.time() - start2 < 7:

                click_any_MS_img(r'images/claim!.PNG', timeout=0)
                click_any_MS_img(r'images/claim_hover.PNG', timeout=0)
                click_any_MS_img(
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    timeout=0
                )

            # Moviendo puntero
            pg.moveTo(10, 10)

            if confirm_initial_images_passed():
                break

        elif click_any_MS_img(
            r'images/start_screen/event_has_ended_sanctum.PNG', timeout=0
        ):
            click_any_MS_img(r'images/x.png')
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)
            
            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)
                click_any_MS_img(r'images/stages/collection_rewards_stage/nice!.PNG', timeout=5)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            if confirm_initial_images_passed():
                break
                
        elif click_any_MS_img(
            r'images/event_has_ended_teamclash.PNG', timeout=0
        ):
            click_any_MS_img(r'images/x.png')
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)
            
            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)
                click_any_MS_img(r'images/stages/collection_rewards_stage/nice!.PNG', timeout=5)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            if confirm_initial_images_passed():
                break
        
        elif click_any_MS_img(r'images/start_screen/image_part_of_event_grand_arena_finished.PNG', timeout=0):
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)
            
            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)
                click_any_MS_img(r'images/stages/collection_rewards_stage/nice!.PNG', timeout=5)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            if confirm_initial_images_passed():
                break
                
        elif search_MS_img(r'images/start_screen/28_day_event_login_rewards.PNG', timeout=0):
            
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)

            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                    r'images/claim_After_receive_new_deck.PNG',
                ]

                while time.time() - start_time < 30:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            elif claim := search_MS_img(r'images/claim_hover.png', timeout=3):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 15:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            if confirm_initial_images_passed():
                break        
        
        elif search_MS_img(r'images/day_event_login.PNG', timeout=0):
            presionar_esc()
            pg.moveTo(10, 10)

            # Buscar cualquiera de los dos botones de reclamo
            claim = search_MS_img(r'images/claim!.PNG', timeout=5) or search_MS_img(r'images/claim_hover.png', timeout=3)

            if claim:
                time.sleep(3)
                click_pos(claim)

                start_time = time.time()
                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 60:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            pg.moveTo(10, 10)
            if confirm_initial_images_passed():
                break    
        
        
        elif search_MS_img(r'images/14_days_event.PNG', timeout=0):
            
            presionar_esc()
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)

            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 60:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            elif claim := search_MS_img(r'images/claim_hover.png', timeout=3):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 15:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            if confirm_initial_images_passed():
                break        
        
        
        elif click_any_MS_img(r'images/lets_go.PNG', timeout=0):
            # Moviendo puntero para evitar distorsion de imagen
            pg.moveTo(10, 10)
            
            if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 90:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            elif claim := search_MS_img(r'images/claim_hover.png', timeout=3):
                time.sleep(3)
                click_pos(claim)

                # Durante unos segundos, intenta detectar y hacer click en
                # todas las pantallas de recompensa que pueden aparecer.
                # No importa el orden ni si alguna no aparece.
                # El loop termina solo por tiempo.
                start_time = time.time()

                images = [
                    r'images/stages/collection_rewards_stage/nice!.PNG',
                    r'images/claim!.PNG',
                    r'images/claim_hover.PNG',
                    r'images/nice_hover_half.PNG',
                ]

                while time.time() - start_time < 20:
                    for img in images:
                        click_any_MS_img(img, timeout=0)
            
            # Moviendo puntero
            pg.moveTo(10, 10)
            
            '''
            if clain := wait_for_image(r'images/claim_recompensas no reclamadas de final de season.PNG'):
                while time.time() - start_time < 10: 
                    click_pos(claim)
            '''
            
            if confirm_initial_images_passed():
                break
        
    
        time.sleep(1)


CURRENT_ACCOUNT = None  # inicializar global

def login(acc):
    """
    Performs the full login process into SNAP using a specific Google account.

    The function automates the UI flow required to authenticate a user.
    It resizes the SNAP window, navigates through the login interface,
    selects the corresponding Gmail account image, and confirms that the
    login succeeded by detecting the Play screen.

    Parameters
    ----------
    acc : str
        Account identifier used to locate the account image inside:
        images/accounts/relogin_accounts/gmail_accounts/vm/{acc}.png

    Process
    -------
    1. Resize the SNAP window to a predefined region.
    2. Click the "submit" button on the main screen.
    3. Wait until the "Sign in with Google" button appears.
    4. Click the Google login button.
    5. Select the Gmail account image corresponding to `acc`.
    6. Handle the temporary focus change to Python.
    7. Return focus to the SNAP application from the taskbar.
    8. Verify successful login by detecting the Play screen.

    Fallback Behavior
    -----------------
    If the Play screen does not appear within the timeout:
    1. Cancel the login dialog.
    2. Repeat the Google login sequence once more.

    Notes
    -----
    Some optional sections are commented out:
    - First-time login flow.
    - FPS configuration (switching from 60 FPS to 30 FPS).
    These can be re-enabled if required for the environment setup.
    """
    
    global CURRENT_ACCOUNT
    CURRENT_ACCOUNT = acc
    
    account_img = rf'images/accounts/relogin_accounts/gmail_accounts/vm/{acc}.png'

    if not os.path.exists(account_img):
        print(f"[ERROR] Account image not found: {account_img}")
        beep_forever()
        raise FileNotFoundError(f"Account image not found: {account_img}")
    
    os.startfile("steam://rungameid/1997040")
    logger.info("[DEBUG] Resizing SNAP window...")
    resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, timeout=5)
    
    if click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2, timeout=90):
        pass
    else:
        search_initial_imgs()
        logout()
        login(acc)
        return
        # click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2, timeout=90)

    time.sleep(2)
    click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2)
    
    resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, timeout=1)
    
    if search_MS_img(r'images/please_sign.png', alert_on_fail=False):
        click_any_MS_img(r'images/ok_btn.png')
        if click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], delay_click=.2, timeout=30):
            click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2)

        else:
            if search_MS_img("images/aw_snap.png", timeout=3):
                click_any_MS_img("images/x.png")
            click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2)
            click_any_MS_img([r'images/small_submit.PNG',r'images/small_submit_hover.png', r'images/submit_hover_2.png', r'images/small_submit_hover_2.png'], region=None, delay_click=.2)

    
    # search_MS_img(r'images/stages/main_stage/sign_in_with_google2.PNG', timeout=90)
    
    # Para setear los fps a 30
    '''
    logger.info("[DEBUG] Haciendo click en posición (691, 955) (nut2)...")
    click_pos((691, 955))  # ⚠️ Depende de la resolución de SNAP definida en globals.REGION_MS_WINDOW
        
    if wait_for_image_and_click(r'images/stages/main_stage/60fps.PNG', timeout=3, confidence=.9):
        logger.info("[DEBUG] '60fps' encontrado, cambiando a '30fps'...")
        wait_for_image_and_click(r'images/stages/main_stage/30fps.PNG')
    
    presionar_esc()
    '''

    click_any_MS_img(r'images/stages/main_stage/sign_in_with_google2.PNG')
        


        
    if search_MS_img(r'images/pagina_cargada.png', timeout=60):
        
        # Buscar la ventana de Chrome y maximizarla
        try:
            chrome_window = gw.getWindowsWithTitle('Google Chrome')[0]
            chrome_window.maximize()
        except IndexError:
            print("No se encontró la ventana de Chrome.")

        time.sleep(2)

        # visual comment: first try full search without scrolling
        if not click_any_MS_img(account_img, region=(0,0,1920,900), delay_click=3, timeout=0):

            # visual comment: fallback scrolling search
            start_time = time.time()

            while time.time() - start_time < 5:
                # visual comment: move mouse to scrollable area before scrolling
                pg.moveTo(500, 500)  

                # visual comment: perform scroll (negative = down)
                pg.scroll(-500)
                time.sleep(0.5)

                if click_any_MS_img(account_img, region=None, delay_click=3, timeout=0):
                    time.sleep(1)
                    break
    
    if search_MS_img(r'images/marvelsnap_web.png', timeout=30, confidence=.7):
        os.system("taskkill /im chrome.exe /f")

       
def logout():
    
    """
    Performs the logout sequence from the SNAP application.

    The function automates the interface navigation required to
    sign out from the currently logged-in account. It assumes the
    process begins from the main screen where the settings icon
    (gear / "nut") is visible.

    Process
    -------
    1. Click the settings icon.
    2. Wait for the settings panel to appear by detecting the
       "graphics_quality" element.
    3. Click the detected element to ensure the settings panel
       has focus.
    4. Scroll down through the settings menu.
    5. Click the logout option.
    6. Confirm the logout through the confirmation dialogs.
    7. Resize the SNAP window back to the predefined region.

    Behavior
    --------
    If the settings panel cannot be detected within the timeout,
    the function stops execution and reports the failure.

    Notes
    -----
    There is an optional section commented out that forcefully
    terminates the SNAP process using taskkill. This can be
    enabled if a hard reset of the application becomes necessary.
    """

    click_any_MS_img(r'images/stages/main_stage/nut.png')
    click_any_MS_img(r'images/graphics_quality.png', timeout=3)

    '''
    a = search_MS_img(r'images/graphics_quality.png', timeout=3)

    if a is None:
        logger.info("[ERROR] graphics_quality image not found.")
        return

    logger.info("[DEBUG] Clicking graphics quality...")
    pg.click(a)
    '''
    
    time.sleep(1)
    pg.scroll(-800)
    click_any_MS_img(r'images/stages/main_stage/sign_out.png')
    time.sleep(1)
    click_any_MS_img(r'images/sign_out_grande.png')
    # Se hace 2 veces en el mismo sign_out2 para deslogear correctamente
    click_any_MS_img(r'images/stages/main_stage/sign_out2.png')
    time.sleep(1)
    click_any_MS_img(r'images/stages/main_stage/sign_out2_hover.png')
    resize_window_by_tuple("SNAP",region=globals.REGION_MS_WINDOW,timeout=2)
    time.sleep(1)
    os.system("taskkill /im snap.exe /f")
    time.sleep(3)


def upgrade_cards(cards_to_upgrade):
    
    
    logger.info("[INFO] Iniciando mejora de cartas")

    # Intenta hacer clic en cualquiera de las dos imágenes
    if not click_any_MS_img([r'images/stages/shop/upgrade_cards_icon.PNG', r'images/stages/shop/upgrade_cards_icon_selected.PNG'], timeout=3):
        logger.warning("[ALERT] No se encontró ninguno de los íconos de upgrade_cards. Saltando función.")
        return

    logger.info("[INFO] Abriendo icono de upgrade_cards")
    time.sleep(1)
    
    cartas_a_mejorar = cards_to_upgrade
    i = 0  # Inicializamos el contador manualmente

    while i < cartas_a_mejorar:
        logger.info(f"[STEP] Mejorando carta {i+1}")

        # Click en cada carta según posición
        pg.click(218 + 150 * i, 580)
        logger.info(f"[ACTION] Click en carta {i+1}")
        time.sleep(1)

        # Primer clic en UPGRADE
        pg.click(374, 889)
        logger.info("[ACTION] Click en botón upgrade")
        time.sleep(7)

        # Confirmación UPGRADE
        pg.click(374, 889)
        
        # --- CASO AW SNAP ---
        if search_MS_img("images/aw_snap.png", timeout=3):
            logger.warning("[ALERT] Se detectó Aw Snap. Reiniciando desde la primera carta...")
            click_any_MS_img("images/x.png")
            
            # Navegación para resetear la pantalla
            click_any_MS_img(r'images/unselected/shop_unselected.PNG')
            click_any_MS_img(r'images/stages/shop/cards_shop.PNG')
            click_any_MS_img(r'images/stages/shop/offers.PNG')
            click_any_MS_img([r'images/stages/shop/upgrade_cards_icon.PNG', r'images/upgrade_cards_icon_selected.png'])
            time.sleep(1)
            
            cartas_a_mejorar = 3  # Aseguramos que intente las 3 cartas
            i = 0                 # <--- CRUCIAL: Reseteamos el contador a la primera carta (0)
            continue              # Salta al inicio del while sin sumar el contador

        # --- CASO FALTA DE CRÉDITOS ---
        if click_any_MS_img(r'images/you_need_more_credits!.png', timeout=3):
            presionar_esc(2)
            time.sleep(2)
            break
            
        # --- CASO ÉXITO ---
        else:
            time.sleep(5)
            # Click para continuar a stage de nivel de coleccion
            pg.click(374, 889)
            logger.info("[ACTION] Click para continuar a stage de nivel de coleccion")
            time.sleep(5)

            # Aqui poner el proceso de obtener rewards
            #collect_cl_rewards()

            # Salir de stage nivel de coleccion
            presionar_esc()
            logger.info("[ACTION] Saliendo de stage nivel de coleccion con ESC")
            time.sleep(1)

        # Reabrir el menú excepto después de la última carta
        if i < cartas_a_mejorar - 1:  # Dinámico según el total de cartas
            start_time = time.time()
            while time.time() - start_time < 3:
                if click_any_MS_img(r'images/stages/shop/upgrade_cards_icon_selected.PNG', timeout=0):
                    break
                if click_any_MS_img(r'images/stages/shop/upgrade_cards_icon.PNG', timeout=0):
                    break

            logger.info("[INFO] Reabriendo icono de upgrade_cards")
            time.sleep(1)

        # Avanzamos a la siguiente carta solo si todo salió bien
        i += 1

    logger.info("[INFO] Mejora de cartas completada ✅")
    

def select_deck(deck):
    if play_location := search_MS_img(r'images/stages/play_stage/play.PNG'):
        pg.moveTo(play_location.x - 160, play_location.y)
        pg.click()
        logger.info("[INFO] Click realizado donde se equipa el deck a jugar")
        
        time.sleep(4)
        
        if deck == '6turns':
            click_any_MS_img(r'images/deck_666666.png', timeout=3)
        elif deck == '3turns':
            click_any_MS_img(r'images/deck_333.png', timeout=3)
            
        if click_any_MS_img(r'images/equip.png', timeout=3, confidence=.95):
            pass
        else:
            presionar_esc()
    

def play_cards_ahk(turns):

    # Hacer los drags
    for start, end in zip(turns, globals.POSITIONS_FIELDS):
        subprocess.run([
            r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
            r"C:\Users\Abel\Documents\SHARED FILES VM\MS\scripts\arrastrar_mouse.ahk",
            str(start[0]), str(start[1]),
            str(end[0]), str(end[1])
        ])

    # Rotar los destinos: el primero pasa al final
    globals.POSITIONS_FIELDS = globals.POSITIONS_FIELDS[1:] + globals.POSITIONS_FIELDS[:1]


def click_blue_missions():

    logger.info("[INFO] Iniciando click_missions_blue2")
    # time.sleep(1)
    click_pos((150, 132), delay_click=1) # Icono de calendar missions basics
    logger.info("[ACTION] Click hecho en icono de calendario que me dirige a las misiones ordinarias")
    
    claim_mission_y_coord = 493
    
    if search_MS_img(r'images/bonus_challenge.png'):
        claim_mission_y_coord = 790
    
    time.sleep(2)

    missions_to_claim = get_completed_missions()

    for i in range(get_completed_missions()):
        click_pos((362, claim_mission_y_coord))
        logger.info(f"[ACTION] Click {i+1}/{missions_to_claim} en misión azul")
        time.sleep(.5)

    if search_MS_img('images/stages/missions_stage/flechita_mission.PNG'):
        logger.info("[INFO] Detectada flechita_mission -> presionando ESC")
        presionar_esc()


def click_blue_missions_2():
    logger.info("[INFO] Iniciando click_missions_blue_2")
    
    click_pos((150, 132), delay_click=1)  # Icono de calendar missions basics
    logger.info("[ACTION] Click hecho en icono de calendario que me dirige a las misiones ordinarias")
    
    claim_mission_y_coord = 493
    if search_MS_img(r'images/bonus_challenge.png'):
        claim_mission_y_coord = 790
        logger.info("[INFO] Imagen bonus_challenge detectada. Coordenada Y ajustada a 790")
    else:
        logger.info("[INFO] No se detectó bonus_challenge. Usando coordenada Y por defecto: 493")
    
    logger.info("[INFO] Esperando 2 segundos antes de iniciar clics...")
    time.sleep(2)

    # 6 clics ininterrumpidos
    for i in range(6):
        click_pos((362, claim_mission_y_coord))
        logger.info(f"[ACTION] Click {i+1}/6 realizado en misión azul")
        time.sleep(0.5)

    # Comprobación final
    logger.info("[CHECK] Verificando si apareció flechita_mission tras los 6 clicks")
    if search_MS_img('images/stages/missions_stage/flechita_mission.PNG'):
        logger.info("[INFO] Detectada flechita_mission -> presionando ESC 1 vez")
        presionar_esc()
    else:
        logger.info("[INFO] No se detectó flechita_mission")

    logger.info("[INFO] Función click_blue_missions_2 terminada")    


def get_weekly_rewards():
    
    start = time.time()
    while time.time() - start < 2:
        
        if click_any_MS_img(r'images/stages/missions_stage/weekly3.PNG', delay_click=.1,timeout=0):
            
            start2 = time.time()
            while time.time() - start2 < 5:
            
                click_any_MS_img(r'images/claim!.PNG', delay_click=.2, timeout=0)
                click_any_MS_img(r'images/claim_hover.PNG', delay_click=.2, timeout=0)

            start = time.time()


def resize_window_by_tuple(
    title_contains: list[str] = None,  # Lista de strings entre corchetes: ["parte_del_titulo1", "parte_del_titulo2"]
    region: tuple = (0, 0, 800, 600),  # Tupla de 4 enteros: (left, top, width, height)
    delay: int = 0.1,                  # Tiempo en segundos antes de iniciar (float o int)
    check_interval: float = 0.1,       # Intervalo en segundos para comprobar cambios (float)
    timeout: int = 0.1,                # Tiempo total en segundos para verificar y reajustar (float o int)
    wait_for_window: int = 20           # Tiempo máximo en segundos para esperar que aparezca la ventana (int)
):
    """
    Redimensiona una ventana según `region`.

    Parámetros:
    - title_contains (list[str] | None): Lista de palabras o fragmentos de título de la ventana a buscar.
      Ejemplo: ["notepad", "python"]. Si se deja None, se usará la ventana activa actual.
      Cada string debe ir entre corchetes y comillas.

    - region (tuple[int, int, int, int]): Tupla con las coordenadas y tamaño deseado: (left, top, width, height).
      Ejemplo: (100, 100, 800, 600)

    - delay (float | int): Segundos a esperar antes de iniciar el redimensionamiento.

    - check_interval (float): Segundos entre verificaciones de cambio de tamaño.

    - timeout (float | int): Tiempo total en segundos para mantener el tamaño deseado y reajustar si cambia.

    - wait_for_window (int): Segundos máximos para esperar a que aparezca una ventana que contenga
      alguno de los textos en `title_contains`.

    Comportamiento:
    - Si la ventana está minimizada o maximizada, la restaura antes de redimensionar.
    - Ajusta la ventana al tamaño y posición indicados en `region`.
    - Verifica durante `timeout` segundos que la ventana mantenga el tamaño y reaplica si cambia.
    - Imprime información sobre cada paso y los reajustes realizados.
    """

    logger.info(f"⏱ Esperando {delay} segundos antes de empezar...")
    time.sleep(delay)

    left, top, width, height = region

    # Esperar a que aparezca una ventana con el título indicado
    if title_contains:
        logger.info(f"🔍 Esperando ventana que contenga alguna de: {title_contains} (máx {wait_for_window}s)")
        start_wait = time.time()
        target_window = None

        while time.time() - start_wait < wait_for_window:
            for win in gw.getAllWindows():
                win_title_lower = win.title.lower()
                if any(word.lower() in win_title_lower for word in title_contains):
                    target_window = win
                    break

            if target_window:
                logger.info(f"✅ Ventana encontrada: '{target_window.title}'")
                break

            time.sleep(check_interval)

        if not target_window:
            logger.info(f"❌ No se encontró ninguna ventana con '{title_contains}' tras {wait_for_window}s")
            return
    else:
        target_window = gw.getActiveWindow()
        if not target_window:
            logger.info("❌ No hay ventana activa para redimensionar.")
            return


    logger.info(f"✅ Ventana seleccionada: '{target_window.title}'")
    
    try:
        target_window.activate()
    except Exception:
        pass
        
    time.sleep(2)

    start_time = time.time()
    reapplied_count = 0

    while time.time() - start_time <= timeout:
        # Si está minimizada o maximizada, restaurarla
        if target_window.isMinimized or target_window.isMaximized:
            logger.info("↗ Ventana minimizada o maximizada. Restaurando...")
            target_window.restore()
            time.sleep(0.3)

        current_state = (target_window.left, target_window.top, target_window.width, target_window.height)

        if current_state != (left, top, width, height):
            reapplied_count += 1
            logger.info(f"🔁 Reajuste #{reapplied_count}...")
            target_window.moveTo(left, top)
            target_window.resizeTo(width, height)

        time.sleep(check_interval)

    if reapplied_count > 0:
        logger.info(f"✔ Verificación completa. Se hicieron {reapplied_count} reajustes.")
    else:
        logger.info("✔ Verificación completa. No hubo cambios después del primer ajuste.")


def get_unclaimed_collection_rewards_count():

    # Abrir y cargar el JSON
    with open(get_nvprod_json_path('CollectionState'), "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Contar elementos
    return len(data["ServerState"]["CollectionScoreRewardDefIdsUnclaimed"]["CollectionScoreRewardDefIds"])


def collect_cl_rewards(resize=False):
    def dbg(message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [DEBUG] {message}")

    dbg("=== INICIANDO FUNCIÓN collect_cl_rewards ===")
    
    # 1. Click inicial y espera solicitados
    dbg("Haciendo click inicial en (387, 166)...")
    click_pos((387, 166))
    update_json_info('CollectionState')
    time.sleep(3)
    
    # 2. Condicional para los resizes según el parámetro
    if resize:
        dbg("Aplicando cambio de tamaño de ventanas...")
        resize_window_by_tuple(["sandbox"], region=globals.REGION_TOTAL_MINUS_MS_WINDOW, wait_for_window=3)
        resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, wait_for_window=3)
    else:
        dbg("Se omitió el cambio de tamaño de ventanas (resize=False)")
    
    remaining_rewards = get_unclaimed_collection_rewards_count()
    dbg(f"Recompensas iniciales detectadas por la API: {remaining_rewards}")
    
    reward_x = 260
    is_first_click = True 

    while remaining_rewards > 0:
        dbg("--------------------------------------------------")
        dbg(f"Inicio de iteración. Recompensas restantes: {remaining_rewards}")
        
        if globals.stop_loop:
            logger.info("Loop stopped manually")
            break

        dbg(f"Intentando hacer click en: ({reward_x}, 580)")
        pg.click(reward_x, 580)
        
        subprocess.run(["taskkill", "/F", "/IM", "notepad++.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

        # Definir región de chequeo según el lado actual
        if reward_x == 260:
            check_region = (228, 547, 65, 55)
        else:
            check_region = (449, 547, 65, 55)

        # Verificar éxito
        claim_detected = search_MS_img(r'images/claim!.PNG', timeout=3)
        credit_detected = False

        if not claim_detected:
            dbg(f"No se detectó 'Claim'. Buscando 'check.png' en región {check_region}...")
            credit_detected = search_MS_img(r'images/check.png', region=check_region, timeout=1)

        success = claim_detected or credit_detected

        # Lógica de corrección en el primer click
        if is_first_click and not success:
            reward_x = 470 if reward_x == 260 else 260
            dbg(f"-> [CORRECCIÓN] Primer click fallido. Cambiando de lado a X = {reward_x}")
            is_first_click = False  
            continue

        is_first_click = False 

        # Procesar el reclamo
        if claim_detected:
            dbg("-> ¡ÉXITO! Botón 'Claim' detectado.")
            if search_MS_img(r'images/stages/collection_rewards_stage/set.png', timeout=2):
                time.sleep(5)
                click_any_MS_img(r'images/claim!.PNG', timeout=0)
                pg.move(-200, -300)
                nice = search_MS_img(r'images/nice!2.PNG', timeout=4)
                if nice:
                    click_pos(nice)
                    pg.move(-200, -300)
            else:
                click_any_MS_img(r'images/claim!.PNG', timeout=0)
        elif credit_detected:
            dbg("-> ¡ÉXITO! Crédito detectado por 'check.png'. Reclamado automáticamente por el click previo.")
        else:
            dbg("-> [ALERTA] No se detectó ninguna recompensa válida tras el click.")

        # Scroll y alternancia normal
        dbg("Moviendo el mouse a la posición de scroll (350, 580)...")
        pg.moveTo(350, 580, duration=0.2)
        for idx in range(8):
            pg.scroll(15)
            time.sleep(0.05)
        
        old_x = reward_x
        reward_x = 470 if reward_x == 260 else 260
        dbg(f"Alternancia de coordenada X: Cambió de {old_x} a {reward_x}")
        
        remaining_rewards -= 1

    print("Finished collecting rewards")
    time.sleep(1)
    presionar_esc()


def is_steam_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
            return True
    return False


def close_steam_windows():
    # Close Steam windows
    to_close = ["Special Offers", "Steam"]
    updating_keywords = ["update", "updating", "downloading", "installing"]

    logger.info("Starting Steam window scan")

    for title in gw.getAllTitles():
        logger.info(f"Found window: {title}")

        for target in to_close:
            if target.lower() in title.lower():
                logger.info(f"Matched target '{target}' in window: {title}")

                windows = gw.getWindowsWithTitle(title)

                if not windows:
                    logger.info(f"No active window found for: {title}")
                    continue

                win = windows[0]

                # --- WAIT WHILE STEAM IS BUSY ---
                while any(keyword in win.title.lower() for keyword in updating_keywords):
                    logger.info(f"Waiting, Steam busy: {win.title}")
                    time.sleep(5)

                    windows = gw.getWindowsWithTitle(title)
                    if not windows:
                        logger.info(f"Window disappeared while waiting: {title}")
                        break

                    win = windows[0]
                # --- END WAIT ---

                # Close window if still exists
                if win:
                    logger.info(f"Closing window: {win.title}")
                    win.close()
                    logger.info(f"Closed window: {win.title}")                


# # CHECK APPDATA NPROV JSON and Get info JSON

def get_unclaimed_collection_rewards_count():
    try:
        with open(get_nvprod_json_path('CollectionState'), "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return len(data["ServerState"]["CollectionScoreRewardDefIdsUnclaimed"]["CollectionScoreRewardDefIds"])
    except Exception as e:
        logger.error("Error leyendo recompensas no reclamadas: %s", e)
        return 0


def get_wallet_amounts():
    try:
        with open(get_nvprod_json_path('ProfileState'), 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        currencies = data.get('ServerState', {}).get('Wallet', {}).get('_currencies', {})
        return {
            'Credits': currencies.get('Credits', {}).get('Credits', {}).get('TotalAmount', 0),
            'Gold': currencies.get('Gold', {}).get('Gold', {}).get('TotalAmount', 0),
            'CollectorsTokens': currencies.get('CollectorsTokens', {}).get('CollectorsTokens', {}).get('TotalAmount', 0)
        }
    except Exception as e:
        logger.error("Error leyendo billetera: %s", e)
        return {'Credits': "ERROR/MISSING", 'Gold': "ERROR/MISSING", 'CollectorsTokens': "ERROR/MISSING"}


def get_collection_level():
    try:
        with open(get_nvprod_json_path('CollectionState'), "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return data["ServerState"]["CollectionScore"]["Amount"]
    except Exception as e:
        logger.error("Error leyendo nivel de colección: %s", e)
        return "ERROR/MISSING"


def procesar_cartas_cuenta(account_name):
    path = get_nvprod_json_path("CollectionState")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        cards = data.get("ServerState", {}).get("Cards", [])
        return [card.get("CardDefId") for card in cards if card.get("CardDefId")]
    except Exception as e:
        print(f"Error en {account_name}: {e}")
        return []
    

def get_deck_card_names(deck_name):
    try:
        with open(get_nvprod_json_path('CollectionState'), 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
        for deck in data['ServerState']['Decks']:
            if deck['Name'] == deck_name:
                return ", ".join([card['CardDefId'] for card in deck['Cards']])
        return "DECK_NOT_FOUND"
    except Exception as e:
        logger.error("Error leyendo cartas del mazo: %s", e)
        return "ERROR/MISSING"


# --- FUNCIONES DE ASISTENCIA ---

def format_duration(seconds):
    """Convierte segundos flotantes a formato legible 'Xm Ys'"""
    try:
        if seconds is None or seconds <= 0:
            return "0m 0s"
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    except Exception:
        return "0m 0s"

