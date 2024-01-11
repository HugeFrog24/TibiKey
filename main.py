import keyboard
import logging
import pyautogui
import pyperclip
import sys
import time

from functools import partial
from PyQt5.QtWidgets import QApplication, QStyle
from openai import OpenAI
from gui.settings_dialog import SettingsDialog
from gui.tray_icon import TrayIcon
from settings_manager import SettingsManager
from utils import get_openai_response

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

settings = SettingsManager(config_file=CONFIG_FILE, defaults_file=PROMPTS_FILE)

api_key = settings.get("api_key")
model = settings.get("model", "gpt-4-1106-preview")
user_prompts = settings.get("hotkeys", {})

# Initialize the OpenAI client only if api_key is available
client = None
if api_key:
    client = OpenAI(api_key=api_key)
    # Now that we have the client, set it in the settings manager
    settings.set_client(client)

# Function to handle the key combination event
def on_triggered(prompt):
    time.sleep(0.5)  # Wait for the keyboard keys to be released before proceeding
    original_clipboard = None  # Initialize to None or an empty string
    max_tokens = settings.get("max_tokens")
    try:
        # Backup the original clipboard content
        original_clipboard = pyperclip.paste()
        logger.debug(f"Original Clipboard content: {original_clipboard}")
        
        # Simulate CTRL+C to copy the highlighted text
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.2)  # Wait a bit for the clipboard content to update.

        # Get the currently highlighted text (copied in the previous step)
        highlighted_text = pyperclip.paste()
        if not highlighted_text.strip():
            logger.warning("No text highlighted.")
            return
        
        logger.debug(f"Highlighted text: {highlighted_text}")

        # Get response from OpenAI
        response = get_openai_response(client, prompt=prompt, text=highlighted_text, max_tokens=max_tokens, model=model)

        # Copy OpenAI response to clipboard
        pyperclip.copy(response)
        time.sleep(0.2)  # Wait a bit for the clipboard content to update

        # Simulate CTRL+V to paste the response automatically
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)  # Wait a bit to ensure the paste operation completes

        # Restore original clipboard content
        pyperclip.copy(original_clipboard)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if original_clipboard is not None:
            pyperclip.copy(original_clipboard)  # Restore only if it was set

# Initialize the application
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Initialize the settings dialog and tray icon
settings_dialog = SettingsDialog(client, settings)
tray_icon = TrayIcon(app.style().standardIcon(QStyle.SP_ComputerIcon), settings_dialog, app)

# Show the settings dialog on application start
settings_dialog.show()

# Start the tray service
tray_icon.show()

logger.info(f"User prompts loaded: {user_prompts}")

# Check for duplicate key combinations in user_prompts
key_combos = [hotkey_info["key_combo"] for _, hotkey_info in user_prompts.items() if isinstance(hotkey_info, dict)]
if len(key_combos) != len(set(key_combos)):
    logger.warning("Duplicate key combinations found in the configuration. Some hotkeys may not work as expected.")

logger.debug("Registering hotkeys...")

# Listen for the key combinations using user_prompts
for action, hotkey_info in user_prompts.items():
    logger.debug(f"Processing action: {action}")
    if isinstance(hotkey_info, dict):
        key_combo = hotkey_info.get("key_combo")
        prompt = hotkey_info.get("prompt", "")  # Default to empty string if not found
        logger.debug(f"Attempting to register hotkey {key_combo} for action '{action}' with prompt '{prompt}'")
        if key_combo is not None and prompt is not None:  # Check for None instead of falsiness
            try:
                keyboard.add_hotkey(key_combo, partial(on_triggered, prompt))
                logger.info(f"Registered hotkey {key_combo} for action '{action}'")
            except Exception as e:
                logger.error(f"Failed to register hotkey {key_combo} for action '{action}': {e}")
        else:
            logger.error(f"Missing 'key_combo' or 'prompt' for action '{action}'")

logger.info("Service running... Press CTRL+R after highlighting text.")

# This is the main loop that will keep the application running
if __name__ == "__main__":
    sys.exit(app.exec_())
