import json
import os
import subprocess
import time
import logging
from src.utils import globals

logger = logging.getLogger(__name__)

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

def get_postgame_xp_value():
    with open(get_nvprod_json_path("BattlePassState"), "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return (
        data.get("ServerState", {})
            .get("BattlePass", {})
            .get("PostGameXpTrackedAmount", 0)
    )

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
