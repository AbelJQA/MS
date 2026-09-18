
import os


def get_missions():
    # Abrir JSON con filepath fijo
    with open(get_nvprod_json_path('MissionState'), 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    # Lista de submisiones
    sub_missions = data['ServerState']['State']['DailyMissionGroup']['SubMissions']

    missions_info = []
    for mission in sub_missions:
        missions_info.append({
            'MissionDefId': mission['MissionDefId'],
            'MissionDifficulty': mission['MissionDifficulty'],
            'RequiredProgress': mission['RequiredProgress'],
            'CurrentProgress': mission.get('CurrentProgress', 0)
        })

    return missions_info


def get_shop_reward_info():
    try:
        with open(get_nvprod_json_path("ShopState"), "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        possible_rewards = (
            data["ServerState"]
            ["CardShopModules"][1]
            ["Items"][2]
            ["AvailableRewardPool"]
            ["PossibleRewards"]
        )

        card_ids = [
            reward.get("Card", {}).get("CardDefId", "")
            for reward in possible_rewards
        ]

        return {
            "possible_rewards_count": len(possible_rewards),
            "card_ids": card_ids
        }

    except Exception as e:
        logger.error("Error leyendo recompensas de tienda: %s", e)
        return {
            "possible_rewards_count": 0,
            "card_ids": []
        }


def guardar_datos_en_txt():
    # Abrir el archivo JSON
    with open(rf'C:\Users\{globals.USER_NAME}\AppData\LocalLow\Second Dinner\SNAP\Standalone\States\nvprod\BattlePassState.json', 'r', encoding='utf-8-sig') as file:
        data = json.load(file)

    # Guardar el valor de la llave "PostGameXpTrackedAmount"
    postgame_xp_tracked_amount = data['ServerState']['BattlePass']['PostGameXpTrackedAmount']

    # Iterar sobre los valores de MSs
    for snap_path in globals.MSs:
        # Guardar los valores en el archivo de texto para cada snap_path
        with open(rf'C:\Users\{globals.USER_NAME}\Desktop\aea.txt', 'a') as file:  # Usamos 'a' para agregar datos al archivo
            file.write(f"{snap_path}: {postgame_xp_tracked_amount}\n")

    logger.info("Datos guardados")


def obtener_postgame_xp(json_file=rf'C:\Users\{os.getlogin()}\AppData\LocalLow\Second Dinner\SNAP\Standalone\States\nvprod\BattlePassState.json'):
    try:
        with open(json_file, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
        return data['ServerState']['BattlePass']['PostGameXpTrackedAmount']
    except KeyError:
        logger.info("⚠️ No se encontró 'PostGameXpTrackedAmount' en el archivo, se omitió este valor.")
        return 0
    except Exception as e:
        logger.info(f"❌ Error al leer el archivo: {e}")
        return 0


def get_series_shop_rewards():
    '''
    Devuelve las cartas de series 4 y 5 que te faltan
    '''
    try:
        with open(get_nvprod_json_path("ShopState"), "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        server_state = data["ServerState"]
        module_1 = server_state.get("CardShopModules", [])[1]
        module_2 = server_state.get("CardShopModules", [])[2]
        
        # Módulo 1, Item 1 (Nuevas cartas Serie 5)
        m1_item1_rewards = []
        try:
            m1_item1_rewards = module_1["Items"][1]["AvailableRewardPool"]["PossibleRewards"]
        except (IndexError, KeyError):
            pass

        # Módulo 1, Item 2 (Nuevas cartas Serie 4)
        m1_item2_rewards = []
        try:
            m1_item2_rewards = module_1["Items"][2]["AvailableRewardPool"]["PossibleRewards"]
        except (IndexError, KeyError):
            pass

        result = {}

        for item_index in [0, 1]:
            try:
                possible_rewards = module_2["Items"][item_index]["AvailableRewardPool"]["PossibleRewards"]
            except (IndexError, KeyError):
                possible_rewards = []

            card_ids = [reward["Card"]["CardDefId"] for reward in possible_rewards]

            # Inyección Serie 5 (item_0)
            if item_index == 0 and m1_item1_rewards:
                for reward in m1_item1_rewards:
                    card_id = reward.get("Card", {}).get("CardDefId")
                    if card_id and card_id not in card_ids:
                        card_ids.append(card_id)

            # Inyección Serie 4 (item_1)
            elif item_index == 1 and m1_item2_rewards:
                for reward in m1_item2_rewards:
                    card_id = reward.get("Card", {}).get("CardDefId")
                    if card_id and card_id not in card_ids:
                        card_ids.append(card_id)

            result[f"item_{item_index}_count"] = len(card_ids)
            result[f"item_{item_index}_cards"] = card_ids

        return result

    except Exception as e:
        logger.error("Error leyendo shop rewards: %s", e)
        return {
            "item_0_count": 0,
            "item_0_cards": [],
            "item_1_count": 0,
            "item_1_cards": []
        }


def alliances_bounties(account):
    logger.info("Iniciando función alliances_bounties()...")

    while True:
        # Buscamos missions_unnotified2 para saber si estamos en la pantalla principal (main)
        if search_MS_img(r'images/stages/main_stage/missions_unnotified2.png', timeout=0):
            break

        time.sleep(1)

    # Ya que estamos en main ahora buscamos alliances
    if click_any_MS_img(
        'images/stages/main_stage/alliances_notification2.png', 
        confidence=0.95,
        delay_click=3,
        timeout=3,
        region=(635,913,707-635,983-913),
        alert_on_fail=False
        ):

        for x, y in globals.slot_bounties:

            time.sleep(5)
            click_pos((x, y))
            time.sleep(1)

            if search_MS_img(r'images/stages/alliances_stage/drop.PNG', timeout=0):
                presionar_esc()

            elif search_MS_img(r'images/stages/alliances_stage/bounty_board.PNG', timeout=0):
                presionar_esc()

        if search_MS_img(r'images/stages/alliances_stage/personal_bounties_complete.PNG', confidence=.85, timeout=1):
            beep_forever()
            presionar_esc()

        else:
            click_any_MS_img('images/stages/alliances_stage/bounty_plus_sign.PNG')

            start_time_while = time.time()
            salir = True
            ejecutar_esc = True
            imagen_encontrada = False

            while (time.time() - start_time_while < 30) and salir:

                for img in globals.imagen_bounties:

                    if bounty := search_MS_img(str(img), region=globals.REGION_BOUNTIES, confidence=.9, timeout=0):

                        click_pos(bounty)
                        click_any_MS_img(r'images/stages/alliances_stage/grab.PNG')
                        imagen_encontrada = True

                        if search_MS_img('images/stages/alliances_stage/unable_to_grab_bounty.PNG'):

                            presionar_esc()
                            capture_screenshot(f'{account}, primary bounties checked and as least one added')
                            presionar_esc(2)

                            salir = False
                            ejecutar_esc = False
                            break

                if not imagen_encontrada:

                    time.sleep(0.3)  # Small pause to avoid excessive CPU usage

            # Paso 2: Si no se encontró ninguna, buscar en la lista secundaria
            if not imagen_encontrada and salir:
                capture_screenshot(f'{account}, primary bounties checked and no one added ')
                #beep_forever()

                for img in globals.imagen_bounties_win_location:

                    if bounty := search_MS_img(str(img), region=globals.REGION_BOUNTIES, timeout=0):
                        logger.info(bounty)
                        click_pos(bounty)
                        click_any_MS_img(r'images/stages/alliances_stage/grab.PNG')

                        if search_MS_img('images/stages/alliances_stage/unable_to_grab_bounty.PNG'):
                            presionar_esc()
                            capture_screenshot(f'{account}, secondary bounties checked and as least one added')
                            presionar_esc(2)
                            ejecutar_esc = False
                        break

            if ejecutar_esc:
                capture_screenshot(f'{account}, all bounties checked')
                presionar_esc(2)

