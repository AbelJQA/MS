print("ESTOY CARGANDO:", __file__)
import re
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
from obsws_python import ReqClient
import shutil
from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill

def beep_forever():
    while True:
        winsound.Beep(500, 500)
        time.sleep(10)

def presionar_esc(veces=1):
    for i in range(veces):
        print(f"Presionando ESC ({i+1}/{veces})")
        keyboard.press('\x1b')
        time.sleep(0.1)
        keyboard.release('\x1b')
        time.sleep(0.3)

def click_pos(pos, delay_click=1):
    # param pos is a tuple
    if pos is None:
        print("click_pos recibió None, no se hace clic")
        return
    x, y = pos
    print(f"Haciendo click en la posición ({x}, {y})")  # <-- print agregado
    pg.moveTo(x, y)
    time.sleep(delay_click)
    pg.click(x, y)
    
def wait_for_port(host, port, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def start_obs_then_record():
    # time.sleep(15)

    ruta_obs = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    carpeta_obs = r"C:\Program Files\obs-studio\bin\64bit"

    obs_activo = any(
        proc.info["name"] == "obs64.exe"
        for proc in psutil.process_iter(["name"])
    )

    if not obs_activo:
        subprocess.Popen(
            [ruta_obs, "--minimize-to-tray", "--disable-shutdown-check"],
            cwd=carpeta_obs
        )

    print("⏳ Esperando WebSocket de OBS...")
    if not wait_for_port("localhost", 4455, timeout=90):
        print("❌ El WebSocket no se levantó")
        return

    client = ReqClient(host="localhost", port=4455, password="")
    print("✅ Conectado al OBS WebSocket")

    for _ in range(20):
        try:
            status = client.get_record_status()
            break
        except Exception:
            time.sleep(1)
    else:
        print("❌ OBS no respondió a tiempo")
        return

    if not status.output_active:
        client.start_record()
        print("🎬 Grabación iniciada")


def end_record_obs():
    client = ReqClient(host="localhost", port=4455, password="")
    client.stop_record()
    print("Record stopped.")

    time.sleep(12)  # Waiting to OBS finish to save

    output_folder = rf"C:\Users\{os.getlogin()}\Videos"
    files = [os.path.join(output_folder, f) for f in os.listdir(output_folder)]
    video_files = [f for f in files if f.lower().endswith(('.mp4', '.mkv'))]

    if not video_files:
        print("Not found records.")
        return

    most_recent_file = max(video_files, key=os.path.getmtime)

    # Agregar fecha y hora actual al nombre
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extension = os.path.splitext(most_recent_file)[1]
    nuevo_nombre = os.path.join(
        output_folder, f"MS_bot_{timestamp}{extension}")

    try:
        shutil.move(most_recent_file, nuevo_nombre)
        print(f"Archivo renombrado a: {nuevo_nombre}")
    except Exception as e:
        print(f"Error al renombrar: {e}")


def buscar_recursivo(estructura, palabra):
    """Busca la palabra (case-insensitive) en cualquier nivel de anidación."""
    resultados = []
    palabra_min = palabra.lower()  # Convertir a minúsculas una sola vez
    
    if isinstance(estructura, dict):
        for k, v in estructura.items():
            if isinstance(v, str) and palabra_min in v.lower():
                resultados.append(f"Clave '{k}': {v}")
            elif isinstance(v, (dict, list)):
                resultados.extend(buscar_recursivo(v, palabra))
                
    elif isinstance(estructura, list):
        for elemento in estructura:
            if isinstance(elemento, str) and palabra_min in elemento.lower():
                resultados.append(f"En lista: {elemento}")
            elif isinstance(elemento, (dict, list)):
                resultados.extend(buscar_recursivo(elemento, palabra))
                
    return resultados


def buscar_palabra_en_varios_archivos_json2(palabra, carpeta = rf'C:\Users\{os.getlogin()}\AppData\LocalLow\Second Dinner\SNAP\Standalone\States\nvprod'):
    """Busca en todos los JSON de la carpeta sin importar mayúsculas/minúsculas."""
    print(f"--- Buscando '{palabra}' (Ignorando mayúsculas/minúsculas) ---\n")
    
    archivos = [a for a in os.listdir(carpeta) if a.endswith(".json")]
    print(f"Se encontraron {len(archivos)} archivos JSON para analizar.\n")
    
    for archivo in archivos:
        ruta = os.path.join(carpeta, archivo)
        print(f"[Leyendo] {archivo}...")
        
        try:
            with open(ruta, "r", encoding="utf-8-sig") as f:
                datos = json.load(f)
            
            coincidencias = buscar_recursivo(datos, palabra)
            
            for coincidencia in coincidencias:
                print(f"  [COINCIDENCIA] {coincidencia}")
                logger.info(f"{archivo} - {coincidencia}")
                
        except Exception as e:
            print(f"  [ERROR] {archivo}: {e}")

    print("\n--- Búsqueda finalizada ---")


def capture_screenshot(label="", save_path="~/Pictures", region=None):
    """
    Captura una captura de pantalla, opcionalmente de una región específica,
    y la guarda en un subdirectorio con la fecha de la primera llamada.

    :param label: Etiqueta para incluir en el nombre del archivo.
    :param save_path: Ruta del directorio raíz para guardar las capturas.
    :param region: Una tupla (left, top, width, height) que define el área a capturar.
                   Si es None, se captura la pantalla completa.
    """
    # 1. Expandir la ruta de inicio del usuario (e.g., "~/Pictures")
    root_path = os.path.expanduser(save_path)
    
    # 2. Verificar y crear el directorio de sesión (solo la primera vez)
    if capture_screenshot.session_dir is None:
        # Generar el nombre de la nueva carpeta basado en la fecha
        fecha_dir = datetime.now().strftime("Capturas_%Y-%m-%d_%H-%M-%S")
        
        # Crear la ruta completa del nuevo directorio
        session_path = os.path.join(root_path, fecha_dir)
        
        # Crear el directorio si no existe
        try:
            os.makedirs(session_path, exist_ok=True)
            logger.info(f"✅ Carpeta de sesión creada: {session_path}")
            
            # Guardar la ruta para usarla en llamadas futuras
            capture_screenshot.session_dir = session_path
        except OSError as e:
            logger.info(f"❌ Error al crear el directorio: {e}")
            # Si hay un error, volvemos a la ruta raíz por seguridad
            capture_screenshot.session_dir = root_path


    # 3. Asignar la ruta de guardado a la carpeta de sesión creada
    filepath_to_save = capture_screenshot.session_dir

    # Sanitizar la etiqueta para el nombre del archivo
    safe_label = re.sub(r'[\\/*?:"<>|]', "_", label)
    
    # Crear el nombre del archivo con la etiqueta y la marca de tiempo
    filename_label = f"_{safe_label}" if safe_label else ""
    filename = datetime.now().strftime(f"screenshot_%H-%M-%S{filename_label}.png")
    
    # Ruta final del archivo
    filepath = os.path.join(filepath_to_save, filename)

    # 4. Tomar la captura: usando la región si se especifica, sino, la pantalla completa
    try:
        if region and isinstance(region, tuple) and len(region) == 4:
            # Captura la región específica: (left, top, width, height)
            screenshot = pg.screenshot(region=region)
            logger.info(f"Capturando región: {region}")
        else:
            # Captura la pantalla completa
            screenshot = pg.screenshot()
            logger.info("Capturando pantalla completa.")
            
        screenshot.save(filepath)
        logger.info(f"Captura guardada en {filepath}")
        
    except Exception as e:
        logger.info(f"❌ Error al tomar o guardar la captura: {e}")

# Variable 'estática' para rastrear si el directorio de la sesión ya existe.
capture_screenshot.session_dir = None
