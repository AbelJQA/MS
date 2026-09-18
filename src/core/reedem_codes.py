import subprocess
from datetime import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

import src.utils.globals as globals
# ============================================================================
# CHROME REMOTE DEBUGGING CONFIGURATION
# ============================================================================

CHROME_COMMAND = (
    r'"C:\Program Files\Google\Chrome\Application\chrome.exe" '
    r'--remote-debugging-port=8989 '
    r'--user-data-dir="c:\chromeData" '
    r'--profile-directory="Default" '
    r'--window-position=660,0 '
    r'--window-size=884,1070 '
    r'https://shop.marvelsnap.com/'
)

print("Launching Chrome with remote debugging")
subprocess.Popen(CHROME_COMMAND, shell=True)

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:8989")

print("Attaching WebDriver to Chrome session")
driver = webdriver.Chrome(options=chrome_options)
print("WebDriver successfully attached")


# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

LOG_PATH = (
    r"C:\Users\Abel\Documents\SHARED FILES VM\MS\logs\reedem_codes.txt"
)

REDEEM_KEY = "AAPI2026"

# Genera la lista dinámicamente usando los nombres activos en globals.py
ACCOUNTS = [f"{name}@gmail.com" for name in globals.accounts]


# ============================================================================
# MAIN FLOW
# ============================================================================

print("Opening Marvel Snap shop homepage")
driver.get("https://shop.marvelsnap.com/")
print(f"Current URL loaded: {driver.current_url}")

for account in ACCOUNTS:
    try:
        print("\n========== NEW ACCOUNT ==========")
        print(f"Account email: {account}")
        print("Starting login flow")

        # --------------------------------------------------------------------
        # LOGIN BUTTON
        # --------------------------------------------------------------------
        print("Waiting for login button")
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#header-67d01278f5e0f7240297b700 "
                    "> div > header > div.header-line__container "
                    "> div.header-line__right > button",
                )
            )
        )

        driver.execute_script("arguments[0].click();", login_button)
        print("Login button clicked")

        # --------------------------------------------------------------------
        # GOOGLE LOGIN BUTTON
        # --------------------------------------------------------------------
        print("Waiting for Google login button")
        google_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-testid="google"]')
            )
        )

        google_button.click()
        print("Current handles:", driver.window_handles)
        print("Current active:", driver.current_window_handle)
        print("Google login button clicked")

        # --------------------------------------------------------------------
        # GOOGLE ACCOUNT SELECTION
        # --------------------------------------------------------------------
        
        print("Waiting for Google account selection")
        account_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f'[data-identifier="{account}"]')
            )
        )

        account_button.click()
        print("Google account selected")

        print("Waiting for page to fully load")
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete"
        )
        print("Page load completed")

        # --------------------------------------------------------------------
        # REDEEM CODE
        # --------------------------------------------------------------------
        try:
            #time.sleep(5)
            print("Opening redeem code page")
            driver.get("https://shop.marvelsnap.com/#promocodes")

            redeem_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "#promocodes > div > div > div.promocodes-v2__content "
                        "> div.promocodes-v2__code-container > div > input",
                    )
                )
            )

            print("Redeem input found")
            redeem_input.clear()
            redeem_input.send_keys(REDEEM_KEY)
            print(f"Redeem code entered: {REDEEM_KEY}")

            print("Waiting for redeem button")
            redeem_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '[id="686e9a208f54f32aa0f58014"]')
                )
            )

            redeem_button.click()
            print("Redeem button clicked")

            print("Waiting for confirmation modal")
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#coupon-modal-button")
                )
            )

            confirm_button.click()
            print("Redeem confirmed successfully")

        except TimeoutException:
            print("Redeem flow timeout detected")
            print("Code already redeemed or not available")

        # --------------------------------------------------------------------
        # LOGOUT
        # --------------------------------------------------------------------
        print("Waiting before logout to allow backend sync")
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

        driver.execute_script("window.scrollTo(0, 0);")
        print("Scrolled to top before logout")

        print("Waiting for logout button")
        logout_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#header-67d01278f5e0f7240297b700 "
                    "> div > header > div.header-line__container "
                    "> div.header-line__right > button",
                )
            )
        )

        driver.execute_script("arguments[0].click();", logout_button)
        print("Logout button clicked")
        
        # --------------------------------------------------------------------
        # LOGOUT DIAGNOSTIC
        # --------------------------------------------------------------------
        print("Checking if logout modal exists in DOM")

        modals = driver.find_elements(
            By.CSS_SELECTOR,
            "div.logout-modal"
        )

        print(f"Logout modals found: {len(modals)}")

        if modals:
            print("Logout modal HTML snippet:")
            print(modals[0].get_attribute("outerHTML")[:500])
        else:
            print("No logout modal found in DOM")

        print("Waiting for logout confirmation modal")
        confirm_logout = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "#site-builder-editor > div.ui-site-modal-window "
                    ".logout-modal > div > div.logout-modal__buttons "
                    "> button.logout-modal__logout-button",
                )
            )
        )

        driver.execute_script("arguments[0].click();", confirm_logout)
        print("Logout confirmed")

        print("Waiting for session to be fully closed")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'button[data-testid="google"]'
                )
            )
        )

        print("Session fully logged out")

    except Exception as error:
        print("Unhandled exception caught")
        print(
            f"Error with {account}: "
            f"{type(error).__name__} - {error}"
        )

        with open(LOG_PATH, "a", encoding="utf-8") as file:
            file.write(
                f"{account} | ERROR | "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                f"{type(error).__name__} | {error}\n"
            )


# ============================================================================
# DO NOT CLOSE THE DRIVER WHEN USING REMOTE DEBUGGING
# ============================================================================

pass