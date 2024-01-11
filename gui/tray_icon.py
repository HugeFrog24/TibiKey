from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

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
