from pathlib import Path

import openai
from openai import OpenAI
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QTextEdit, QVBoxLayout)

from utils import get_openai_models, validate_max_tokens, validate_model


class SettingsDialog(QDialog):
    LOG_FILE = "app.log"

    def __init__(self, client, settings):
        super().__init__()
        self.client = client
        self.settings = settings

        self.setWindowTitle("Your Service Name")
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowMinimizeButtonHint)
        self.setMinimumWidth(600)

        self.mainLayout = QVBoxLayout()

        # General settings section
        self.generalSettingsGroup = QGroupBox("General")
        self.generalLayout = QVBoxLayout()

        self.apiKeyLayout = QHBoxLayout()
        self.apiKeyLabel = QLabel("OpenAI API Key:")
        self.apiKeyEdit = QLineEdit()
        self.apiKeyLayout.addWidget(self.apiKeyLabel)
        self.apiKeyLayout.addWidget(self.apiKeyEdit)

        self.modelLayout = QHBoxLayout()
        self.modelLabel = QLabel("Model:")
        self.modelComboBox = QComboBox()
        self.modelComboBox.currentIndexChanged.connect(self.onModelChanged)
        self.modelLayout.addWidget(self.modelLabel)
        self.modelLayout.addWidget(self.modelComboBox)

        self.maxTokensLayout = QHBoxLayout()
        self.maxTokensLabel = QLabel("Max Tokens:")
        self.maxTokensEdit = QLineEdit()
        self.maxTokensLayout.addWidget(self.maxTokensLabel)
        self.maxTokensLayout.addWidget(self.maxTokensEdit)

        self.streamLayout = QHBoxLayout()
        self.streamLabel = QLabel("Stream Responses:")
        self.streamCheckBox = QCheckBox()
        self.streamLayout.addWidget(self.streamLabel)
        self.streamLayout.addWidget(self.streamCheckBox)

        self.importLayout = QHBoxLayout()
        self.importLabel = QLabel("Import settings:")
        self.importButton = QPushButton("Load file...")
        self.importButton.clicked.connect(self.importConfig)
        self.importLayout.addWidget(self.importLabel)
        self.importLayout.addWidget(self.importButton)

        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.saveSettings)

        # Add widgets to the general settings layout
        self.generalLayout.addLayout(self.apiKeyLayout)
        self.generalLayout.addLayout(self.modelLayout)
        self.generalLayout.addLayout(self.maxTokensLayout)
        self.generalLayout.addLayout(self.streamLayout)
        self.generalLayout.addLayout(self.importLayout)
        self.generalLayout.addWidget(self.saveButton)

        # Set the layout for the general settings group
        self.generalSettingsGroup.setLayout(self.generalLayout)

        # Log section
        self.logGroup = QGroupBox("Log")
        self.logLayout = QVBoxLayout()
        self.logTextBox = QTextEdit(self)
        self.logLayout.addWidget(self.logTextBox)

        # Set the layout for the log group
        self.logGroup.setLayout(self.logLayout)

        # Add groups to the main layout
        self.mainLayout.addWidget(self.generalSettingsGroup)
        self.mainLayout.addWidget(self.logGroup)

        self.setLayout(self.mainLayout)

        # Load existing settings
        self.loadSettings()

        # Start the timer to update the log
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateLog)
        self.timer.start(1000)  # Update every 1000ms (1 second)

    def setApiKey(self, api_key):
        self.apiKeyEdit.setText(api_key)

    def importConfig(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "JSON Files (*.json)", options=options)
        if fileName:
            self.settings.load(Path(fileName))
            self.loadSettings()

    def loadSettings(self):
        try:
            max_tokens = self.settings.get("max_tokens", 256)
            allowed_tokens_range = self.settings.get(
                "allowed_tokens_range", [1, 4096])
            validate_max_tokens(max_tokens, allowed_tokens_range)

            self.apiKeyEdit.setText(self.settings.get("api_key", ""))

            # Clear the modelComboBox before adding new items
            self.modelComboBox.clear()

            # Populate the modelComboBox with available models only if client
            # is not None
            if self.client:
                available_models = get_openai_models(self.client)
                self.modelComboBox.addItems(available_models)

            # Enable the modelComboBox if it contains any models
            self.modelComboBox.setEnabled(self.modelComboBox.count() > 0)

            # Find the index of the model from settings and set it
            model_from_config = self.settings.get("model")
            model_index = self.modelComboBox.findText(model_from_config)
            if model_index != -1:
                self.modelComboBox.setCurrentIndex(model_index)
            else:
                # Set to first model if not found
                self.modelComboBox.setCurrentIndex(0)

            self.maxTokensEdit.setText(str(max_tokens))
            self.streamCheckBox.setChecked(self.settings.get("stream", False))
        except Exception as e:
            QMessageBox.warning(
                self,
                "Settings Load Error",
                f"Could not load settings: {e}")

    def onModelChanged(self, index):
        model = self.modelComboBox.currentText()
        if model and model != self.settings.get("model"):
            self.settings.set("model", model)

    def saveSettings(self):
        try:
            max_tokens = int(self.maxTokensEdit.text())
            allowed_tokens_range = self.settings.get(
                "allowed_tokens_range", [1, 4096])
            validate_max_tokens(max_tokens, allowed_tokens_range)
            api_key = self.apiKeyEdit.text()

            api_key_changed = api_key != self.settings.get("api_key")
            if api_key_changed:
                self.client = OpenAI(api_key=api_key)
                self.settings.set_client(self.client)
                models = get_openai_models(self.client)
                if models:
                    self.modelComboBox.clear()
                    self.modelComboBox.addItems(models)
                else:
                    QMessageBox.warning(
                        self, "Invalid API Key", "The provided API key is invalid.")
                    return  # Do not save settings or close the dialog

            # Validate and set the model only if necessary
            model = self.modelComboBox.currentText()
            if model != self.settings.get("model"):
                validate_model(model, self.client)
                self.settings.set("model", model)

            self.settings.set("api_key", api_key)
            self.settings.set("max_tokens", max_tokens)
            self.settings.set("stream", self.streamCheckBox.isChecked())

            self.settings.save()  # Ensure settings are saved to the file
        except openai.AuthenticationError as e:
            QMessageBox.critical(self, "Authentication Error", str(e))
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def updateLog(self):
        try:
            with open(self.LOG_FILE) as f:
                log_content = f.read()
                if self.logTextBox.toPlainText() != log_content:
                    self.logTextBox.setPlainText(log_content)
                    cursor = self.logTextBox.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.logTextBox.setTextCursor(cursor)
        except FileNotFoundError:
            pass
