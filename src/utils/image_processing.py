from datetime import datetime
import logging
import pyautogui as pg
import time
import os
import cv2
import numpy as np
import easyocr
import winsound
from src.utils import globals

logger = logging.getLogger(__name__)

# Asumo que 'reader' ya está inicializado en tu script globalmente:
# Variable global interna (empieza vacía para no ralentizar el 'import')
_reader = None

def _get_reader():
    """Inicializa el lector de EasyOCR solo cuando es estrictamente necesario."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['es'])
    return _reader

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
                from src.utils.my_functions import beep_forever
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
                from src.utils.my_functions import beep_forever
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
    if isinstance(paths, str):
        paths = [paths]

    kwargs.pop('quick_check', None)
    kwargs.pop('timeout', None)

    start_time = time.time()
    
    logger.info(
        f"[DEBUG] Buscando en paralelo: {[os.path.basename(p) for p in paths]} "
        f"| timeout={timeout}s | confidence={confidence}"
    )

    while True:
        for path in paths:
            position = search_MS_img(
                path,
                timeout=0, 
                region=region,
                confidence=confidence,
                quick_check=True,
                verbose=False,
                **kwargs,
            )

            if position:
                from src.utils.my_functions import click_pos
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

def search_MS_text_ocr(
        path_or_text,
        timeout=0,
        confidence=0.35, 
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
    reader = _get_reader()

    while True:
        elapsed = time.time() - start_time
        position = None

        try:
            screenshot = pg.screenshot(region=region)
            image_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            results = reader.readtext(image_cv, paragraph=False, text_threshold=confidence)

            for bbox, text, prob in results:
                text_clean = text.strip().upper()

                if palabra_buscar_clean in text_clean and prob >= confidence:
                    puntos_en_pantalla = [tuple(map(int, p)) for p in bbox]
                    top_left = puntos_en_pantalla[0]
                    bottom_right = puntos_en_pantalla[2]

                    centro_x = int((top_left[0] + bottom_right[0]) / 2)
                    centro_y = int((top_left[1] + bottom_right[1]) / 2)

                    carpeta_exito = "exito_ocr"
                    if not os.path.exists(carpeta_exito):
                        os.makedirs(carpeta_exito)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    palabra_segura = "".join([c for c in str(path_or_text) if c.isalpha() or c.isdigit()]).rstrip()
                    nombre_archivo_exito = f"{carpeta_exito}/exito_{palabra_segura}_{timestamp}.png"

                    cv2.rectangle(image_cv, top_left, bottom_right, (0, 255, 0), 2)
                    cv2.imwrite(nombre_archivo_exito, image_cv)

                    if region:
                        centro_x += region[0]
                        centro_y += region[1]

                    position = (centro_x, centro_y)
                    break 

        except Exception as e:
            if verbose:
                logger.info(
                    f"[ERROR] Exception while searching text "
                    f"'{path_or_text}' -> {e}"
                )
            if alert_on_fail:
                from src.utils.my_functions import beep_forever
                beep_forever()
            return None

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

        if elapsed > timeout:
            if verbose:
                logger.info(
                    f"\n⛔ Text not found: '{path_or_text}' "
                    f"after {round(elapsed, 2)}s "
                    f"region={region} confidence={confidence}"
                )

            if screenshot is not None:
                carpeta_errores = "errores_ocr"
                if not os.path.exists(carpeta_errores):
                    os.makedirs(carpeta_errores)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                palabra_segura = "".join([c for c in str(path_or_text) if c.isalpha() or c.isdigit()]).rstrip()
                nombre_archivo_error = f"{carpeta_errores}/error_{palabra_segura}_{timestamp}.png"
                screenshot.save(nombre_archivo_error)

            if alert_on_fail:
                from src.utils.my_functions import beep_forever
                beep_forever()

            return None

        time.sleep(interval_searching if interval_searching > 0 else 0.1)

def click_any_MS_text_ocr(
    paths, 
    timeout=20, 
    delay_click=1, 
    region=globals.REGION_MS_WINDOW, 
    confidence=0.35, 
    **kwargs
):
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
                from src.utils.my_functions import click_pos
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
