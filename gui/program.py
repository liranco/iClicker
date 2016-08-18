import os
import sys
from PySide.QtGui import *
from PySide.QtCore import *
from settings import Settings, ServerSettings, ClientSettings
from settings_dialog import SettingsDialog
from notification_widget import NotificationDialog
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
        """
        :type parent: MainWindow
        """
        super(Menu, self).__init__("Mazgan Clicker", parent=parent)
        self.text, self.color = (None, None)
        self.status_label = QLabel(' ' * 20)
        status_label_action = QWidgetAction(self)
        status_label_action.setDefaultWidget(self.status_label)
        self.addAction(status_label_action)
        self.addSeparator()
        dance_action = self.addAction('Dance')
        click_action = self.addAction('Click')
        auto_click_action = self.addAction('Auto Click')
        dance_action.triggered.connect(lambda: parent.client.dance())
        click_action.triggered.connect(lambda: parent.client.click())
        auto_click_action.triggered.connect(parent.show_auto_click)
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
    update_notifications_signal = Signal(tuple)

    def __init__(self, parent=None, flags=0):
        super(MainWindow, self).__init__(parent, flags)
        self.tray = QSystemTrayIcon(icon=QIcon(os.path.join(os.path.dirname(__file__), 'icon2.png')), parent=self)
        self.tray_menu = Menu(self)  # type: Menu
        self.settings = Settings()
        self.active_server_threads = []
        self.settings_dialog = None
        self.client = None
        self._auto_clicker_interval = None
        self._auto_clicker_seconds_left_for_interval = None
        self._connect_to_server_thread = None  # type: ConnectToServerThread
        self._client_connection_check_timer = None
        self._update_auto_clicker_interval_timer = None
        self.notification_widget = None  # type: NotificationDialog
        self._notifications_queue = []
        self._notifications_passed = 0
        self.update_notifications_signal.connect(lambda message: self._show_notification(*message))
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

    def show_auto_click(self):
        print 'Auto Click'
        interval, accepted = QInputDialog().getInt(self,
                                                   'Set Auto Clicker Interval',
                                                   'Please enter interval (in minutes):',
                                                   10, 1)
        if accepted:
            self.client.set_auto_clicker(interval)

    def start_server(self):
        from client import Client
        self.disconnect_client()
        self.stop_server()
        from server import answer_search_requests, run_server
        self.active_server_threads.extend((answer_search_requests(threaded=True),
                                           run_server(threaded=True,
                                                      updates_method=lambda title, body:
                                                      self.update_notifications_signal.emit((title, body)))))
        self.tray_menu.status_label.setText('Hello')
        self.client = Client('127.0.0.1', ServerSettings().server_port,
                             ServerSettings().server_password,
                             client_name=ServerSettings().server_name,
                             is_password_hashed=True)
        self.connect_to_server()

    def _show_notification(self, title, body):
        self._notifications_queue.append((title, body))
        if len(self._notifications_queue) > 1:
            if self.notification_widget:
                self.notification_widget.remaining_notifications += 1
                self.notification_widget.notifications_count_updated.emit()
            return
        self._next_notification()

    def _next_notification(self):
        while len(self._notifications_queue) > 0:
            title, body = self._notifications_queue[0]
            self.notification_widget = NotificationDialog(self, title, body, len(self._notifications_queue) - 1,
                                                          self._notifications_passed)
            self._notifications_passed += 1
            self.notification_widget.exec_()
            self._notifications_queue.pop(0)
        self._notifications_passed = 0

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
        server_options = self._connect_to_server_thread.server_info
        self._auto_clicker_interval = server_options.get('auto_clicker_interval')
        self._auto_clicker_seconds_left_for_interval = server_options.get('auto_clicker_seconds_left_for_interval')
        del self._connect_to_server_thread
        self._connect_to_server_thread = None
        if not self._client_connection_check_timer:
            self._client_connection_check_timer = self.startTimer(5000)
        if not self._update_auto_clicker_interval_timer:
            self._update_auto_clicker_interval_timer = self.startTimer(1000)
        print server_options

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
        if event.timerId() == self._update_auto_clicker_interval_timer:
            if self._auto_clicker_interval is None:
                return
            self._auto_clicker_seconds_left_for_interval -= 1
            print '>>> {}'.format(self._auto_clicker_seconds_left_for_interval)
            if self._auto_clicker_seconds_left_for_interval == 0:
                self._auto_clicker_seconds_left_for_interval = self._auto_clicker_interval


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
        self.server_info = None
        assert isinstance(parent, MainWindow)
        super(ConnectToServerThread, self).__init__(parent)

    def parent(self):
        # type: () -> MainWindow
        return super(ConnectToServerThread, self).parent()

    def run(self):
        import errno
        from client import Client, BadPasswordException, error
        if self.client is None:
            if ClientSettings().connected_server is None:
                self.status_updated.emit((STATUS_CLIENT_NOT_SET, ))
                return
            client = Client()
        else:
            client = self.client
        self.status_updated.emit((STATUS_CLIENT_CONNECTING, client.server_name))
        try:
            server_info = client.connect()
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
            self.server_info = server_info
            self.status_updated.emit((STATUS_CLIENT_CONNECTED, client.server_name))
