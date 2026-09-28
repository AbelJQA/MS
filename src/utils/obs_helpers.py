import logging
import psutil
import subprocess
import time
from datetime import datetime
from obsws_python import ReqClient
import os
import shutil

logger = logging.getLogger(__name__)

record_start_time = None


def wait_for_port(host, port, timeout=60):
    import socket

    start = time.time()

    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)

    return False


def start_obs_then_record():
    global record_start_time

    ruta_obs = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
    carpeta_obs = r"C:\Program Files\obs-studio\bin\64bit"

    logger.info(f"Python ejecutándose desde: {os.getcwd()}")
    logger.info(f"Usuario: {os.getlogin()}")
    z_path = "Z:\\" # test git
    logger.info(f"Z existe: {os.path.exists(z_path)}")
    unc_path = r'\\vmware-host\Shared Folders'
    logger.info(f"Ruta UNC: {os.path.exists(unc_path)}")

    obs_activo = any(
        proc.info["name"] == "obs64.exe"
        for proc in psutil.process_iter(["name"])
        if proc.info["name"]
    )

    if not obs_activo:
        logger.info("OBS no está abierto. Iniciándolo...")

        subprocess.Popen(
            [
                ruta_obs,
                "--minimize-to-tray",
                "--disable-shutdown-check"
            ],
            cwd=carpeta_obs,
            shell=False
        )

    else:
        logger.info("OBS ya estaba abierto.")

    logger.info("⏳ Esperando WebSocket de OBS...")

    if not wait_for_port("localhost", 4455, timeout=90):
        logger.error("❌ El WebSocket de OBS no se levantó.")
        return

    try:
        client = ReqClient(
            host="localhost",
            port=4455,
            password=""
        )

        logger.info("✅ Conectado al OBS WebSocket")

    except Exception as e:
        logger.error(f"❌ Error conectando con OBS: {e}")
        return

    for _ in range(20):
        try:
            status = client.get_record_status()
            break
        except Exception:
            time.sleep(1)

    else:
        logger.error("❌ OBS no respondió a tiempo.")
        return

    if status.output_active:
        logger.info("⏹ Grabación ya estaba activa. Deteniéndola...")

        end_record_obs()

        time.sleep(3)

        client.start_record()

    else:
        client.start_record()

    record_start_time = datetime.now()

    logger.info("🎬 Nueva grabación iniciada")


def end_record_obs():
    global record_start_time

    client = ReqClient(
        host="localhost",
        port=4455,
        password=""
    )

    client.stop_record()

    logger.info("⏹ Record stopped.")

    time.sleep(12)

    output_folder = os.path.join(
        os.path.expanduser("~"),
        "Videos"
    )

    files = [
        os.path.join(output_folder, f)
        for f in os.listdir(output_folder)
    ]

    video_files = [
        f for f in files
        if f.lower().endswith((".mp4", ".mkv"))
    ]

    if not video_files:
        logger.error("❌ No se encontraron grabaciones.")
        return

    most_recent_file = max(
        video_files,
        key=os.path.getmtime
    )

    if record_start_time is None:
        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    else:
        timestamp = record_start_time.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

    extension = os.path.splitext(
        most_recent_file
    )[1]

    nuevo_nombre = os.path.join(
        output_folder,
        f"recording_{timestamp}{extension}"
    )

    try:
        shutil.move(
            most_recent_file,
            nuevo_nombre
        )

        logger.info(
            f"Archivo renombrado a: {nuevo_nombre}"
        )

    except Exception as e:
        logger.error(
            f"Error al renombrar: {e}"
        )