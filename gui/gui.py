import os
import sys
from PySide.QtGui import QSystemTrayIcon, QMenu, QApplication, QIcon, QMainWindow
from settings import Settings
from settings_dialog import SettingsDialog
from consts import *


class Menu(QMenu):
    def __init__(self, parent):
        # type: (MainWindow) -> object
        super(Menu, self).__init__("Mazgan Clicker", parent=parent)

        settings_action = self.addAction('Settings')
        settings_action.triggered.connect(self.open_settings)
        exit_action = self.addAction('Exit')
        exit_action.triggered.connect(parent.close)

    def open_settings(self):
        SettingsDialog(parent=self).exec_()


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=0):
        super(MainWindow, self).__init__(parent, flags)
        self.settings = Settings()
        self.active_server_threads = []
        if self.settings.mode == SERVER_MODE:
            self.start_server()

        self.tray = QSystemTrayIcon(icon=QIcon(os.path.join(os.path.dirname(__file__), 'icon2.png')),
                                    parent=self)
        self.tray.setContextMenu(Menu(self))
        self.tray.show()

    def start_server(self):
        from server import answer_search_requests, run_server
        self.active_server_threads.extend((answer_search_requests(threaded=True),
                                           run_server(threaded=True)))

    def closeEvent(self, event):
        for thread, server in self.active_server_threads:
            server.shutdown()
            server.server_close()
            thread.join()
        super(MainWindow, self).closeEvent(event)
        # noinspection PyArgumentList
        QApplication.instance().exit()



def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    app.setActiveWindow(window)
    app.exec_()
