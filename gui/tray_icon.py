from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QAction  # Corrected import for QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon, dialog, app, parent=None):
        super().__init__(icon, parent)
        self.dialog = dialog
        self.app = app
        self.setToolTip("Your Service Name")

        # Create the menu
        self.menu = QMenu()
        settings_action = QAction("Your Service Name", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        self.menu.addAction(settings_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QCoreApplication.instance().quit)
        self.menu.addAction(quit_action)

        # Set the "Your Service Name" entry to be bold
        font = settings_action.font()
        font.setBold(True)
        settings_action.setFont(font)

        self.setContextMenu(self.menu)

        # Connect the activated signal to a slot
        self.activated.connect(self.on_activated)

        self.show()

    def on_activated(self, reason):
        # On some platforms, this is equivalent to double-click
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_settings_dialog()

    def show_settings_dialog(self):
        self.dialog.show()
