import sys
from PySide.QtGui import QSystemTrayIcon, QMenu, QApplication, QIcon, QMessageBox
from utils import Settings
from settings_dialog import SettingsDialog
from consts import *


class Menu(QMenu):
    def __init__(self):
        super(Menu, self).__init__("Mazgan Clicker")
        self.settings = Settings()
        if self.settings.mode == SERVER_MODE:
            self.announce()
        find_action = self.addAction('Find')
        find_action.triggered.connect(self.find)
        settings_action = self.addAction('Settings')
        settings_action.triggered.connect(self.open_settings)
        exit_action = self.addAction('Exit')
        exit_action.triggered.connect(sys.exit)

    def announce(self):
        from server import answer_search_requests
        print 'announcing'
        answer_search_requests()

    def find(self):
        from client import find_servers
        print find_servers()

    def open_settings(self):
        SettingsDialog().exec_()
        print 'out'


class Tray(QSystemTrayIcon):
    def __init__(self):
        super(Tray, self).__init__()
        self.setIcon(QIcon(r'C:\ProgramData\Razer\GameScanner\Data\GameIcons\24172759-3403-4b90-b09b-2f2bb16fa1de.ico'))
        self.setContextMenu(Menu())


def main():
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setQuitOnLastWindowClosed(False)
    tray = Tray()
    tray.show()
    app.exec_()
