import json
from pathlib import Path

from utils import validate_model


class SettingsManager:
    def __init__(self, config_file, defaults_file):
        self.config_file = Path(config_file)
        self.defaults_file = Path(defaults_file) if defaults_file else None
        self.client = None  # Store the client object
        self.settings = {}
        self.user_settings = {}  # Store only user-modified settings
        self.load()

    def load(self, config_file=None):
        # Load defaults first, if available
        if self.defaults_file and self.defaults_file.exists():
            with open(self.defaults_file) as f:
                self.settings = json.load(f)

        # Override with user settings
        config_file = config_file or self.config_file
        if config_file.exists():
            with open(config_file) as f:
                self.user_settings = json.load(f)
                # Remove settings from user_settings if they are the same as
                # the defaults
                for key in list(
                        self.user_settings):  # Use list to avoid RuntimeError for changing dict size during iteration
                    if key in self.settings and self.user_settings[key] == self.settings[key]:
                        self.user_settings.pop(key)
                # Merge remaining user settings over defaults
                self.settings.update(self.user_settings)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):

        # Validate the model if the key is 'model' and the client is set
        if key == "model" and self.client is not None:
            validate_model(value, self.client)

        # Load default settings to compare
        default_settings = {}
        if self.defaults_file and self.defaults_file.exists():
            with open(self.defaults_file) as f:
                default_settings = json.load(f)

        # Check if the value is different from the default
        if key not in default_settings or default_settings[key] != value:
            self.user_settings[key] = value
            # Update the current settings as well
            self.settings[key] = value
        else:
            # If the value is the same as the default, remove it from
            # user_settings
            self.user_settings.pop(key, None)
            # Ensure the current settings has the default value
            if key in default_settings:
                self.settings[key] = default_settings[key]

        # Save only the user_settings to the config file
        self.save()

    def set_client(self, client):
        self.client = client

    def save(self):
        # Write only the user_settings to the config file
        with open(self.config_file, "w") as f:
            json.dump(self.user_settings, f, indent=4)

    def reset(self):
        self.settings = {}
        self.save()

    def save_models_to_cache(self, models):
        cache_file = "models_cache.json"
        with open(cache_file, "w") as f:
            json.dump(models, f)

    def load_models_from_cache(self):
        cache_file = "models_cache.json"
        if Path(cache_file).exists():
            with open(cache_file, "r") as f:
                return json.load(f)
        return []