import os
import sys
from PySide.QtGui import *
from PySide.QtCore import *
from settings import Settings
from settings_dialog import SettingsDialog
from consts import *


STATUS_CLIENT_NOT_SET = (u"Server Not Configured", Qt.red)
STATUS_CLIENT_CONNECTING = (u'Connecting to {}...', Qt.darkYellow)
STATUS_CLIENT_OFFLINE = (u'{} is Offline', Qt.red)
STATUS_CLIENT_CONNECTED = (u'Connected to {}!', Qt.darkGreen)
STATUS_CLIENT_ERROR = (u'Error #{} on {}!', Qt.red)
STATUS_CLIENT_BAD_PASSWORD = (u'{}\'s password is wrong!', Qt.red)


def get_status_formatted(status, *args):
    return status[0].format(*args), status[1]


class Menu(QMenu):
    def __init__(self, parent):
        super(Menu, self).__init__("Mazgan Clicker", parent=parent)
        self.text, self.color = (None, None)
        self.status_label = QLabel(' ' * 20)
        status_label_action = QWidgetAction(self)
        status_label_action.setDefaultWidget(self.status_label)
        self.addAction(status_label_action)
        self.addSeparator()
        dance_action = self.addAction('Dance')
        dance_action.triggered.connect(lambda: parent.client.dance())
        self.addSeparator()
        settings_action = self.addAction('Settings')
        settings_action.triggered.connect(parent.show_settings)
        exit_action = self.addAction('Exit')
        exit_action.triggered.connect(parent.close)

    def set_status_label(self, text, color):
        self.text, self.color = text, color
        palette = self.status_label.palette()
        palette.setColor(self.status_label.foregroundRole(), color)
        self.status_label.setPalette(palette)
        self.status_label.setText(text)
        self.status_label.setToolTip(text)


class MainWindow(QMainWindow):
    def __init__(self, parent=None, flags=0):
        super(MainWindow, self).__init__(parent, flags)
        self.tray = QSystemTrayIcon(icon=QIcon(os.path.join(os.path.dirname(__file__), 'icon2.png')), parent=self)
        self.tray_menu = Menu(self)  # type: Menu
        self.settings = Settings()
        self.active_server_threads = []
        self.settings_dialog = None
        self.client = None
        self._connect_to_server_thread = None  # type: ConnectToServerThread
        self._client_connection_check_timer = None
        if self.settings.mode == SERVER_MODE:
            self.start_server()
        else:
            self.connect_to_server()

        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()

    def show_settings(self):
        if self.settings_dialog:
            self.settings_dialog.activateWindow()
        else:
            self.settings_dialog = SettingsDialog(self)
            new_mode = self.settings_dialog.exec_()
            self.settings_dialog.deleteLater()
            self.settings_dialog = None
            if new_mode == SERVER_MODE:
                self.start_server()
            elif new_mode == CLIENT_MODE:
                self.stop_server()
                self.connect_to_server()

    def start_server(self):
        from client import Client
        self.disconnect_client()
        from server import answer_search_requests, run_server
        self.active_server_threads.extend((answer_search_requests(threaded=True),
                                           run_server(threaded=True)))
        self.tray_menu.status_label.setText('Hello')
        self.client = Client('127.0.0.1', self.settings.server_settings.server_port,
                             self.settings.server_settings.server_password,
                             client_name='Localhost',
                             is_password_hashed=True)
        self.connect_to_server()

    def stop_server(self):
        self.disconnect_client()
        while len(self.active_server_threads) > 0:
            thread, server = self.active_server_threads.pop()
            if server:
                server.shutdown()
                server.server_close()
            del server
            del thread

    def disconnect_client(self):
        if self.client:
            self.client.close()
            self.client = None
        if self._client_connection_check_timer:
            self.killTimer(self._client_connection_check_timer)
            self._client_connection_check_timer = None

    def connect_to_server(self):
        if self._connect_to_server_thread is None:
            thread = ConnectToServerThread(self, client=self.client)
            thread.status_updated.connect(self.status_updated)
            thread.finished.connect(self.connect_to_server_finished)
            self._connect_to_server_thread = thread
            self._connect_to_server_thread.start()

    def connect_to_server_finished(self):
        self.client = self._connect_to_server_thread.client
        del self._connect_to_server_thread
        self._connect_to_server_thread = None
        if not self._client_connection_check_timer:
            self._client_connection_check_timer = self.startTimer(5000)

    def status_updated(self, status):
        (status_text, status_color), args = status
        args = (args, ) if isinstance(args, basestring) else args
        status_text = status_text.format(*args)
        self.tray_menu.set_status_label(status_text, status_color)
        self.tray.setToolTip(status_text)

    def closeEvent(self, event):
        if self._client_connection_check_timer:
            self.killTimer(self._client_connection_check_timer)
        self.stop_server()
        self.disconnect_client()
        super(MainWindow, self).closeEvent(event)
        # noinspection PyArgumentList
        QApplication.instance().exit()

    def timerEvent(self, event):
        if event.timerId() == self._client_connection_check_timer:
            self.connect_to_server()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    app.setActiveWindow(window)
    app.exec_()


class ConnectToServerThread(QThread):
    status_updated = Signal(tuple)

    def __init__(self, parent, client=None):
        self.client = client
        assert isinstance(parent, MainWindow)
        super(ConnectToServerThread, self).__init__(parent)

    def parent(self):
        # type: () -> MainWindow
        return super(ConnectToServerThread, self).parent()

    def run(self):
        import errno
        from client import Client, BadPasswordException, error
        if self.client is None:
            if self.parent().settings.client_settings.connected_server is None:
                self.status_updated.emit((STATUS_CLIENT_NOT_SET, ))
                return
            client = Client()
        else:
            client = self.client
        self.status_updated.emit((STATUS_CLIENT_CONNECTING, client.server_name))
        try:
            client.connect()
        except BadPasswordException:
            self.status_updated.emit((STATUS_CLIENT_BAD_PASSWORD, client.server_name))
        except error as e:
            if e.errno in (errno.ECONNREFUSED, errno.ETIMEDOUT, errno.ECONNRESET):
                self.status_updated.emit((STATUS_CLIENT_OFFLINE, client.server_name))
            else:
                self.status_updated.emit((STATUS_CLIENT_ERROR, e.errno, client.server_name))
            print e
            client.close()
        else:
            self.client = client
            self.status_updated.emit((STATUS_CLIENT_CONNECTED, client.server_name))
