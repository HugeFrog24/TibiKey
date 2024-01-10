import json
import keyboard
import logging
import pyautogui
import pyperclip
import time
from openai import OpenAI
from PyQt5.QtWidgets import QApplication, QStyle
from gui import SettingsDialog, TrayIcon
import sys

CONFIG_FILE = "config.json"

# Configure the logging module
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# Load existing settings or create default settings
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        
    # Check if the API key is a string and is not empty
    if not isinstance(config["api_key"], str) or not config["api_key"].strip():
        raise ValueError(f"Invalid OpenAI API key. Please ensure the API key in {CONFIG_FILE} is a non-empty string.")
        
except (FileNotFoundError, json.JSONDecodeError):
    config = {
        "api_key": "",
        "hotkeys": {
            "proofread": "ctrl+r",
            "fact_check": "ctrl+t"
        }
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
except ValueError as e:
    logger.error(str(e))
    exit(1)

# Load prompts or create default prompts
try:
    with open("prompts.json", "r") as f:
        prompts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    prompts = {
        "proofread": "Please proofread and give me the corrected text without extra explanations.",
        "fact_check": "Please fact check and correct the following text."
    }
    with open("prompts.json", "w") as f:
        json.dump(prompts, f, indent=4)

client = OpenAI(api_key=config["api_key"])

def get_openai_response(prompt, text):
    try:
        formatted_text = f"{prompt}\n\n{text}"
        response = client.chat.completions.create(
          model="gpt-4-1106-preview",
          messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": formatted_text}
            ],
          max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {e}")
        return ""


# Function to handle the key combination event
def on_triggered(prompt):
    try:
        # Save current clipboard content
        original_clipboard = pyperclip.paste()

        # Simulate CTRL+C to copy highlighted text
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.1)  # wait for clipboard to update

        # Get copied text
        highlighted_text = pyperclip.paste()
        if not highlighted_text.strip():
            logger.warning("No text highlighted.")
            return

        # Get response from OpenAI
        response = get_openai_response(prompt=prompt, text=highlighted_text)

        # Copy OpenAI response to clipboard
        pyperclip.copy(response)

        # Simulate CTRL+V to paste the response
        pyautogui.hotkey("ctrl", "v")

        # Restore original clipboard content after a short delay
        time.sleep(0.1)
        pyperclip.copy(original_clipboard)

    except Exception as e:
        logger.error(f"An error occurred: {e}")

# Initialize the application
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

# Initialize the settings dialog and tray icon
settings_dialog = SettingsDialog()
tray_icon = TrayIcon(app.style().standardIcon(QStyle.SP_ComputerIcon), settings_dialog, app)

# Start the tray service
tray_icon.show()

# Listen for the key combinations
for action, hotkey in config["hotkeys"].items():
    keyboard.add_hotkey(hotkey, lambda action=action: on_triggered(prompts[action]))

logger.info("Service running... Press CTRL+R after highlighting text.")

# This is the main loop that will keep the application running
if __name__ == "__main__":
    sys.exit(app.exec_())