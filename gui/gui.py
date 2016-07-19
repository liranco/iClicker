import os
import sys
from PySide.QtGui import QSystemTrayIcon, QMenu, QApplication, QIcon
from settings import Settings
from settings_dialog import SettingsDialog
from consts import *


class Menu(QMenu):
    def __init__(self):
        super(Menu, self).__init__("Mazgan Clicker")
        self.settings = Settings()
        if self.settings.mode == SERVER_MODE:
            self.announce()
        settings_action = self.addAction('Settings')
        settings_action.triggered.connect(self.open_settings)
        exit_action = self.addAction('Exit')
        exit_action.triggered.connect(sys.exit)

    def announce(self):
        from server import answer_search_requests
        answer_search_requests()

    def open_settings(self):
        SettingsDialog(parent=self).exec_()


class Tray(QSystemTrayIcon):
    def __init__(self):
        super(Tray, self).__init__()
        self.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon2.png')))
        self.setContextMenu(Menu())


def main():
    app = QApplication(sys.argv)
    # app.setStyle('Cleanlooks')
    app.setQuitOnLastWindowClosed(False)
    tray = Tray()
    tray.show()
    app.exec_()
