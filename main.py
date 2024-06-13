import logging
import sys
import time
from functools import partial

import keyboard
import openai
import pyautogui
import pyperclip
from openai import OpenAI
# Ensure PyQt6 is used if you've migrated
from PyQt6.QtWidgets import QApplication, QStyle

from gui.settings_dialog import SettingsDialog
from gui.tray_icon import TrayIcon
from settings_manager import SettingsManager
from utils import get_openai_non_stream_response, get_openai_stream_response

CONFIG_FILE = "config.json"
PROMPTS_FILE = "defaults.json"
LOG_FILE = "app.log"

# Configure the logging module
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the application first
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

settings = SettingsManager(config_file=CONFIG_FILE, defaults_file=PROMPTS_FILE)

api_key = settings.get("api_key")
model = settings.get("model")
user_prompts = settings.get("hotkeys", {})

# Initialize the OpenAI client only if api_key is available
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
        # Now that we have the client, set it in the settings manager
        settings.set_client(client)
    except openai.AuthenticationError as e:
        logger.error(f"Invalid API key: {e}")

# Initialize the settings dialog and tray icon after QApplication
settings_dialog = SettingsDialog(client, settings)
# Correct the icon retrieval method
tray_icon = TrayIcon(
    app.style().standardIcon(
        QStyle.StandardPixmap.SP_DesktopIcon),
    settings_dialog,
    app)

# Function to handle the key combination event
def on_triggered(prompt):
    time.sleep(0.5)
    original_clipboard = pyperclip.paste()
    max_tokens = settings.get("max_tokens")
    stream = settings.get("stream", False)
    try:
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.2)
        highlighted_text = pyperclip.paste()
        if not highlighted_text.strip():
            logger.warning("No text highlighted.")
            return

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": highlighted_text}
        ]

        if stream:
            response_generator = get_openai_stream_response(
                client, messages=messages, max_tokens=max_tokens, model=model)
            for content in response_generator:
                pyperclip.copy(content)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.2)
        else:
            response = get_openai_non_stream_response(
                client, messages=messages, max_tokens=max_tokens, model=model)
            pyperclip.copy(response)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.2)

        pyperclip.copy(original_clipboard)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if original_clipboard is not None:
            pyperclip.copy(original_clipboard)

# Show the settings dialog on application start
settings_dialog.show()

# Start the tray service
tray_icon.show()

logger.info(f"User prompts loaded: {user_prompts}")

# Check for duplicate key combinations in user_prompts
key_combos = [
    hotkey_info["key_combo"] for _,
    hotkey_info in user_prompts.items() if isinstance(
        hotkey_info,
        dict)]
if len(key_combos) != len(set(key_combos)):
    logger.warning(
        "Duplicate key combinations found in the configuration. Some hotkeys may not work as expected.")

logger.debug("Registering hotkeys...")

# Listen for the key combinations using user_prompts
for action, hotkey_info in user_prompts.items():
    logger.debug(f"Processing action: {action}")
    if isinstance(hotkey_info, dict):
        key_combo = hotkey_info.get("key_combo")
        # Default to empty string if not found
        prompt = hotkey_info.get("prompt", "")
        logger.debug(f"Attempting to register hotkey {key_combo} for action '{action}' with prompt '{prompt}'")
        if key_combo is not None and prompt is not None:  # Check for None instead of falsiness
            try:
                keyboard.add_hotkey(key_combo, partial(on_triggered, prompt))
                logger.info(
                    f"Registered hotkey {key_combo} for action '{action}'")
            except Exception as e:
                logger.error(f"Failed to register hotkey {key_combo} for action '{action}': {e}")
        else:
            logger.error(
                f"Missing 'key_combo' or 'prompt' for action '{action}'")

logger.info("Service running... Press CTRL+R after highlighting text.")

# This is the main loop that will keep the application running
if __name__ == "__main__":
    sys.exit(app.exec())
