def verificar_si_sigue_buscando_jugador():
    # Para asegurar que no se quedó bugeado buscando jugador
    while True:
        if search_MS_img(r'images/stages/play_stage/end_turn.PNG', timeout=45):
            logger.info("[INFO] Se encontró end_turn, saliendo del bucle de verificación")
            break
        else:
            logger.info("[WARN] No se encontró end_turn, intentando salir con ESC y volver a Play")
            presionar_esc()
            time.sleep(2)
            click_any_MS_img(r'images/stages/play_stage/play.PNG')
