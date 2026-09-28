from src.utils.debug_screenshots import debug_screenshot
import time
import os
from datetime import datetime
from pathlib import Path
import pandas as pd  # Requerido para exportar a Excel

from logger_config import logger

import pyautogui as pg
from src.utils.globals import *
from src.utils.my_functions import *
from src.utils.obs_helpers import end_record_obs, start_obs_then_record


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
globals.set_mode("normal_6t")

# Lista global para recolectar la información de Excel
excel_report_data = []

try:
    start_obs_then_record()
    pg.moveTo(1500, 100)
    subprocess.run(["taskkill", "/im", "snap.exe", "/f"], check=False)
    logger.info("snap.exe terminated if it was running")
    resize_window_by_tuple(title_contains=["py", "eight_hours"], region=globals.REGION_TOTAL_MINUS_MS_WINDOW)
    
    for account in globals.accounts:
        account_start_time = time.time()
        logger.info("Processing account: %s", account)
        
        # Inicializar métricas del reporte para esta cuenta
        game_durations = []
        games_played_counter = 0
        deck_used = "6turns"
        
        os.startfile("steam://rungameid/1997040")
        resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW)
        login(account)
        search_initial_imgs()
        # update_json_info('ProfileState')
        update_json_info('CollectionState')
        
        # Selección directa del deck sin evaluar misiones
        select_deck("6turns")
        logger.info("Deck selected: 6turns")

        click_any_MS_img(r'images/start_screen/maybe_later.PNG', timeout=2)
        click_any_MS_img(r'images/start_screen/maybe_later2.PNG', timeout=0.01)

        for game_index in range(globals.total_games):
            logger.info("Starting game loop %s", game_index + 1)
            game_start_time = time.time()

            if click_any_MS_img("images/stages/play_stage/play.PNG", delay_click=3):
                games_played_counter += 1
                
                while not search_MS_img("images/stages/play_stage/collect_rewards.PNG", quick_check=True):
                    end_turn = search_MS_img("images/stages/play_stage/end_turn.PNG", quick_check=True)

                    if end_turn:
                        click_any_MS_img("images/stages/play_stage/snap.PNG", quick_check=True, timeout=0)
                        play_cards_ahk(globals.POSITIONS_MOUSE_6_TURNS)
                        if click_any_MS_img("images/stages/play_stage/end_turn.PNG", timeout=0):
                            logger.info("End turn executed")

                    never = search_MS_img("images/stages/play_stage/never_seen_before.png", quick_check=True, timeout=0)
                    if never:
                        pg.moveTo(never)
                        pg.move(0, 300)
                        time.sleep(0.3)
                        pg.click()
                        logger.warning("Unknown popup handled")

                    if search_MS_img("images/aw_snap.png", timeout=0, quick_check=True):
                        time.sleep(2)
                        presionar_esc()
                        logger.warning("aw_snap detected")
                        click_any_MS_img([r'images/play_hover.png', r'images\stages\main_stage\reconnect_to_game.PNG'], timeout=5)

                    if search_MS_img(rf"C:\Users\{os.getlogin()}\OneDrive\my_py_projects\MS\images\stages\play_stage\flechas.png", timeout=0, quick_check=True):
                        time.sleep(2)
                        presionar_esc()
                        click_any_MS_img("images/stages/play_stage/end_turn.PNG", quick_check=True, timeout=0)
                        logger.warning("Arrow overlay handled")

                    if search_MS_img(r'images/failed_to_join_game_error.png'):
                        time.sleep(1)
                        presionar_esc()
                        break

                # Fin del juego actual
                duration = round(time.time() - game_start_time, 2)
                game_durations.append(duration)
                logger.info("Rewards detected, exiting match. Game duration: %s s", duration)

                click_any_MS_img("images/stages/play_stage/collect_rewards.PNG")
                click_any_MS_img("images/stages/play_stage/next.PNG")
            
            elif search_MS_img(r'images/start_screen/28_day_event_login_rewards.PNG', timeout=0):
                presionar_esc()
                pg.moveTo(10, 10)

                if claim := search_MS_img(r'images/claim!.PNG', timeout=5):
                    time.sleep(3)
                    click_pos(claim)
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
                
                pg.moveTo(10, 10)
                if confirm_initial_images_passed():
                    break
            
            time.sleep(2)

            if search_MS_img(r'images/hyper_cube.png', timeout=5):
                click_any_MS_img(r'images/finish_btn.png')

        after_finish_all_games()
        collect_cl_rewards()
        
        # Recolectar datos finales de la cuenta antes del logout
        # wallet = get_wallet_amounts()
        total_account_seconds = time.time() - account_start_time
        
        # Cálculo del promedio de duración por juego
        avg_game_seconds = sum(game_durations) / len(game_durations) if game_durations else 0
        
        excel_report_data.append({
            'Account Name': account,
            'Total Duration': format_duration(total_account_seconds),
            'Games Played': games_played_counter,
            'Promedio Duración Games': format_duration(avg_game_seconds),
            'Deck Cards': get_deck_card_names('666666'),
            'Collection Level': f"{get_collection_level():,}",
            # 'Credits': f"{wallet['Credits']:,}",
            # 'Gold': f"{wallet['Gold']:,}",
            # 'Collectors Tokens': f"{wallet['CollectorsTokens']:,}"
        })
        
        logout()

    # --- EXPORTAR EXCEL ---
    try:
        REPORTS_DIR = Path(__file__).resolve().parent / "reportes"
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(excel_report_data)
        report_filename = REPORTS_DIR / f"Reporte_Ejecucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Guardar en Excel ajustando el ancho de columnas
        with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte')
            worksheet = writer.sheets['Reporte']
            
            # Autoajustar el ancho de las columnas con un margen extra
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 4, 12)

        logger.info("Reporte Excel guardado con éxito en: %s", report_filename)
    except Exception as e:
        logger.error("No se pudo generar el Excel del reporte: %s", e)

    end_record_obs()
    logger.info("OBS recording stopped")
    subprocess.run(["shutdown", "/s", "/t", "0"], check=False)   
    
except Exception:
    logger.exception("Unhandled exception occurred")