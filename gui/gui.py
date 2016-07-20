import os
import sys
from PySide.QtGui import *
from PySide.QtCore import Qt
from settings import Settings
from settings_dialog import SettingsDialog
from consts import *


STATUS_CLIENT_NOT_SET = (u"Server Not Configured", Qt.red)
STATUS_CLIENT_CONNECTING = (u'Connecting to "{}"...', Qt.darkYellow)
STATUS_CLIENT_OFFLINE = (u'"{}" is Offline', Qt.red)
STATUS_CLIENT_CONNECTED = (u'Connected to "{}"!', Qt.darkGreen)
STATUS_CLIENT_ERROR = (u'Error on "{}"!', Qt.red)
STATUS_CLIENT_BAD_PASSWORD = (u'"{}"\'s password is wrong!', Qt.red)


def get_status_formatted(status, *args):
    return status[0].format(*args), status[1]


class Menu(QMenu):
    def __init__(self, parent):
        super(Menu, self).__init__("Mazgan Clicker", parent=parent)
        self.status_label = QLabel('Hi There!')
        status_label_action = QWidgetAction(self)
        status_label_action.setDefaultWidget(self.status_label)
        self.addAction(status_label_action)
        self.addSeparator()
        settings_action = self.addAction('Settings')
        settings_action.triggered.connect(self.open_settings)
        exit_action = self.addAction('Exit')
        exit_action.triggered.connect(parent.close)

    def open_settings(self):
        SettingsDialog(parent=self).exec_()

    def set_status_label(self, status, *args):
        text, color = status
        palette = self.status_label.palette()
        palette.setColor(self.status_label.foregroundRole(), color)
        self.status_label.setPalette(palette)
        self.status_label.setText(text.format(*args))


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=0):
        super(MainWindow, self).__init__(parent, flags)
        self.tray = QSystemTrayIcon(icon=QIcon(os.path.join(os.path.dirname(__file__), 'icon2.png')), parent=self)
        self.tray_menu = Menu(self)  # type: Menu
        self.settings = Settings()
        self.active_server_threads = []
        self.client = None
        if self.settings.mode == SERVER_MODE:
            self.start_server()
        else:
            self.connect_to_server()

        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()

    def start_server(self):
        from server import answer_search_requests, run_server
        self.active_server_threads.extend((answer_search_requests(threaded=True),
                                           run_server(threaded=True)))
        self.tray_menu.status_label.setText('Hello')

    def stop_server(self):
        for thread, server in self.active_server_threads:
            server.shutdown()
            server.server_close()
            thread.join()

    def disconnect_client(self):
        if self.client:
            self.client.close()
            self.client = None

    def connect_to_server(self):
        import errno
        from client import Client, BadPasswordException, error
        if self.settings.client_settings.connected_server is None:
            self.tray_menu.set_status_label(STATUS_CLIENT_NOT_SET)
            return
        client = Client()
        self.tray_menu.set_status_label(STATUS_CLIENT_CONNECTING, client.server_address)
        try:
            client.connect()
        except BadPasswordException:
            self.tray_menu.set_status_label(STATUS_CLIENT_BAD_PASSWORD, client.server_address)
            return
        except error as e:
            if e.errno == errno.ECONNREFUSED:
                self.tray_menu.set_status_label(STATUS_CLIENT_OFFLINE, client.server_address)
            else:
                self.tray_menu.set_status_label(STATUS_CLIENT_ERROR, client.server_address)
            return
        self.client = client
        self.tray_menu.set_status_label(STATUS_CLIENT_CONNECTED, client.server_address)

    def closeEvent(self, event):
        self.stop_server()
        self.disconnect_client()
        super(MainWindow, self).closeEvent(event)
        # noinspection PyArgumentList
        QApplication.instance().exit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    app.setActiveWindow(window)
    app.exec_()
