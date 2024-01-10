import json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (QAction, QDialog, QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QSystemTrayIcon, QTextEdit, QVBoxLayout)

CONFIG_FILE = "config.json"

class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()

        self.setWindowTitle("Settings")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
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


    def importConfig(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "JSON Files (*.json)", options=options)
        if fileName:
            with open(fileName, 'r') as f:
                config = json.load(f)
                self.apiKeyEdit.setText(config["api_key"])

    def loadSettings(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.apiKeyEdit.setText(config["api_key"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def saveSettings(self):
        config = {
            "api_key": self.apiKeyEdit.text(),
            "hotkeys": {
                "proofread": "ctrl+r",
                "fact_check": "ctrl+t"
            }
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        self.close()

    def updateLog(self):
        try:
            with open("app.log", "r") as f:
                self.logTextBox.setPlainText(f.read())
                cursor = self.logTextBox.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.logTextBox.setTextCursor(cursor)
        except FileNotFoundError:
            pass

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, dialog, app, parent=None):
        super(TrayIcon, self).__init__(icon, parent)
        self.dialog = dialog
        self.app = app
        self.setToolTip("Your Service Name")
        
        # Create the menu
        self.menu = QMenu()
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        self.menu.addAction(settings_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(quit_action)
        
        self.setContextMenu(self.menu)
        self.show()

    def show_settings_dialog(self):
        self.dialog.show()
