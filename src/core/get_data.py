import time
import os
import logging
from datetime import datetime
from pathlib import Path
import sys
import pyautogui as pg
import src.utils.globals as globals
import pandas as pd
from src.utils.my_functions import *

globals.set_mode("normal_6t")

try:
    print("=" * 80)
    print("SCRIPT STARTED")
    print("=" * 80)

    print("Moving mouse...")
    pg.moveTo(1500, 100)

    print("Closing SNAP if running...")
    os.system("taskkill /im snap.exe /f")

    print("Starting OBS recording...")
    start_obs_then_record()

    print("Resizing Python window...")
    resize_window_by_tuple(
        title_contains=["py", "eight_hours"],
        region=globals.REGION_TOTAL_MINUS_MS_WINDOW
    )

    rows = []

    total_accounts = len(globals.accounts)
    print(f"Total accounts to process: {total_accounts}")

    for index, account in enumerate(globals.accounts, start=1):
        try:
            print("\n" + "=" * 80)
            print(f"ACCOUNT {index}/{total_accounts}")
            print(f"Processing account: {account}")
            print("=" * 80)

            print("Launching Marvel Snap...")
            os.startfile("steam://rungameid/1997040")

            print("Resizing SNAP window...")
            resize_window_by_tuple(
                ["SNAP"],
                region=globals.REGION_MS_WINDOW
            )

            print("Logging in...")
            login(account)
            print("Login completed")

            print("Searching initial images...")
            search_initial_imgs()
            print("Initial images found")

            print("Opening shop...")
            click_any_MS_img(r'images/shop_icon.png')

            print("Waiting 3 seconds...")
            time.sleep(3)

            print("Pressing ESC...")
            presionar_esc()

            print("Updating MissionState...")
            update_json_info("MissionState")

            print("Updating ProfileState...")
            update_json_info("ProfileState")

            print("Updating CollectionState...")
            update_json_info("CollectionState")
            
            print("Updating CollectionState...")
            update_json_info("ShopState")

            print("Closing popups...")
            click_any_MS_img(
                r'images/start_screen/maybe_later.PNG',
                timeout=2
            )

            click_any_MS_img(
                r'images/start_screen/maybe_later2.PNG',
                timeout=0.01
            )

            print("Getting wallet amounts...")
            wallet = get_wallet_amounts()

            print(
                f"Wallet -> Credits: {wallet['Credits']} | "
                f"Gold: {wallet['Gold']} | "
                f"Tokens: {wallet['CollectorsTokens']}"
            )

            print("Getting missions...")
            missions = get_missions()

            completed_missions = sum(
                1
                for m in missions
                if m["CurrentProgress"] >= m["RequiredProgress"]
            )

            print(
                f"Missions completed: "
                f"{completed_missions}/{len(missions)}"
            )

            print("Getting Collection Level...")
            collection_level = get_collection_level()

            print("Getting unclaimed rewards...")
            unclaimed_rewards = get_unclaimed_collection_rewards_count()

            print(f"Collection Level: {collection_level}")
            print(f"Unclaimed Rewards: {unclaimed_rewards}")
            
            shop_info = get_shop_reward_info()

            print(shop_info["possible_rewards_count"])
            print(shop_info["card_ids"])

            row = {
                "Account": account,
                "CollectionLevel": collection_level,
                "UnclaimedRewards": unclaimed_rewards,
                "Credits": wallet["Credits"],
                "Gold": wallet["Gold"],
                "CollectorsTokens": wallet["CollectorsTokens"],

                "CreditLevelsPotential": wallet["Credits"] / 50,
                "UnclaimedPotential": unclaimed_rewards / 4,
                "TokensPotential": (wallet["Credits"] + unclaimed_rewards) // 30 * 3000,
                "TotalTokensPotential": ((wallet["Credits"] + unclaimed_rewards) // 30 * 3000) + wallet["CollectorsTokens"],
                
                "PossibleRewardsCount": shop_info["possible_rewards_count"],
                "PossibleRewardCards": ",".join(shop_info["card_ids"]),

                "TotalMissions": len(missions),
                "CompletedMissions": completed_missions,
                "CaptureDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            rows.append(row)

            print("Data added to output list")

            print("Logging out...")
            logout()

            print(f"Account completed successfully: {account}")

        except Exception as e:
            print(f"ERROR PROCESSING ACCOUNT: {account}")
            print(str(e))
            logger.exception(
                f"Error while processing account {account}"
            )

    print("\n" + "=" * 80)
    print("SAVING CSV")
    print("=" * 80)

    df = pd.DataFrame(rows)

    print(f"Rows collected: {len(df)}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_name = f"accounts_info_{timestamp}.csv"
    
    df.to_csv(
        csv_name,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"CSV saved: {csv_name}")

    print("CSV saved: accounts_info.csv")

    print("Stopping OBS recording...")
    end_record_obs()

    print("OBS recording stopped")

    print("=" * 80)
    print("SCRIPT FINISHED SUCCESSFULLY")
    print("=" * 80)

    # beep_forever()
    # os.system("shutdown /s /t 0")

except Exception:
    print("\nFATAL ERROR")
    logger.exception("Unhandled exception occurred")