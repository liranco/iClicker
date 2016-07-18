from PySide.QtGui import *
from PySide.QtCore import *
from settings import Settings
from consts import *

settings = Settings()


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle('Mazgan Settings')
        layout = QVBoxLayout()
        self.mode = QComboBox(self)
        self.mode.addItems((CLIENT_MODE, SERVER_MODE))

        self.settings_groups = QStackedWidget(self)
        self.settings_groups.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_groups.addWidget(ClientSettings(self))
        self.settings_groups.addWidget(ServerSettings(self))

        self.mode.currentIndexChanged.connect(self.mode_changed)

        mode_container = QWidget(self)
        mode_container.setLayout(QFormLayout())
        mode_container.layout().addRow("Select Your Mode: ", self.mode)
        layout.addWidget(mode_container)
        layout.addWidget(self.settings_groups)

        self.buttons_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Apply | QDialogButtonBox.Cancel,
                                            parent=self)
        self.buttons_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.buttons_box)

        self.setLayout(layout)

        self.mode.setCurrentIndex(self.mode.findText(settings.mode))

    def mode_changed(self, new_mode_index):
        self.settings_groups.setCurrentIndex(new_mode_index)
        new_mode = self.settings_groups.currentWidget()
        new_mode.activated()

    def closeEvent(self, event):
        for widget in (self.settings_groups.widget(i) for i in xrange(self.settings_groups.count())):
            widget.closed()


class ServerSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(title="Server Settings", parent=parent)
        layout = QFormLayout()
        self.server_name = QLineEdit(parent=self)
        self.server_port = QSpinBox(parent=self)
        self.server_port.setMaximum(65535)
        self.server_password = QLineEdit(parent=self)
        self.server_password.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        self.server_password.changed = False
        self.server_password.textChanged.connect(self.password_changed)
        layout.addRow("Server Name:", self.server_name)
        layout.addRow("Server Port:", self.server_port)
        layout.addRow("Password:", self.server_password)
        layout.addRow(QPushButton('Calibrate Clicker', parent=self))
        self.setLayout(layout)

    def password_changed(self):
        self.server_password.changed = True

    def activated(self):
        self.server_name.setText(settings.server_settings.server_name)
        self.server_port.setValue(settings.server_settings.server_port)
        self.server_password.setText('x' * settings.server_settings.server_password[1])

    def closed(self):
        pass


class ClientSettings(QGroupBox):
    LOAD_SERVERS_TEXT = "Load Servers"
    STOP_LOADING_SERVERS_TEXT = "Click to Stop."

    CURRENT_SERVER_NOT_SET = ("Not Set", Qt.red)
    CURRENT_SERVER_CONNECTING = ('Connecting to "{}"...', Qt.darkYellow)
    CURRENT_SERVER_OFFLINE = ('"{}" is Offline', Qt.red)
    CURRENT_SERVER_CONNECTED = ('Connected to "{}"!', Qt.green)
    CURRENT_SERVER_ERROR = ('Error on "{}"!', Qt.red)

    def __init__(self, parent=None):
        super(ClientSettings, self).__init__(title="Client Settings", parent=parent)
        layout = QFormLayout()
        self.client_name = QLineEdit(parent=self)
        layout.addRow("Client Name", self.client_name)
        current_server_row = QWidget(parent=self)
        current_server_row.setLayout(QHBoxLayout())
        current_server_row.layout().setContentsMargins(0, 0, 0, 0)
        self.current_server_ip = QLineEdit(parent=current_server_row)
        self.current_server_ip.setPlaceholderText("IP Address")
        self.current_server_port = QSpinBox(parent=current_server_row)
        self.current_server_port.setMaximum(65535)
        self.current_server_message = QLabel(parent=current_server_row)
        self._set_current_server_message(*self.CURRENT_SERVER_NOT_SET)
        current_server_row.layout().addWidget(self.current_server_ip)
        current_server_row.layout().addWidget(self.current_server_port)
        current_server_row.layout().addWidget(self.current_server_message)
        # current_server_row.setVisible(False)
        layout.addRow("Current Server:", current_server_row)
        # Setup servers search
        self.servers = QListWidget(self)
        self.servers.currentItemChanged.connect(self.server_picked_from_list)
        layout.addRow('Pick a server:', self.servers)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Hello World")
        self.progress_bar.setHidden(True)
        layout.addRow(self.progress_bar)
        self.reload_servers_button = QPushButton(self.LOAD_SERVERS_TEXT)
        self.reload_servers_button.clicked.connect(self.reload_servers)
        layout.addRow(self.reload_servers_button)
        self.setLayout(layout)
        self.servers_finder_thread = None

    def _set_current_server_message(self, message, color):
        palette = QPalette()
        palette.setColor(QPalette.WindowText, color)
        self.current_server_message.setPalette(palette)
        self.current_server_message.setText(message)

    def reload_servers(self):
        # First, empty the list
        if self.servers_finder_thread is None:
            self.servers.clear()
            self.servers_finder_thread = ServersFinderThread(self)
            self.servers_finder_thread.server_found.connect(self.server_search_found_item)
            self.servers_finder_thread.text_changed.connect(
                lambda text: self.reload_servers_button.setText("%s %s" % (text, self.STOP_LOADING_SERVERS_TEXT)))
            self.servers_finder_thread.started.connect(self.server_search_started)
            self.servers_finder_thread.finished.connect(self.server_search_finished)
            self.servers_finder_thread.start()
        else:
            self.servers_finder_thread.stop_me()

    def server_search_started(self):
        self.progress_bar.setVisible(True)
        self.reload_servers_button.setText(self.STOP_LOADING_SERVERS_TEXT)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)

    def server_search_found_item(self, server_info):
        server_name, ip_address, port = server_info
        item = QListWidgetItem("{} ({}:{})".format(server_name, ip_address, port), view=self.servers)
        item.setData(Qt.UserRole, (server_name, ip_address, port))

    def server_search_finished(self):
        self.progress_bar.setVisible(False)
        del self.servers_finder_thread
        self.servers_finder_thread = None
        self.reload_servers_button.setText(self.LOAD_SERVERS_TEXT)

    def server_picked_from_list(self, item):
        if item is None:
            return
        server_name, ip_address, port = item.data(Qt.UserRole)
        self.current_server_ip.setText(ip_address)
        self.current_server_port.setValue(port)

    def activated(self):
        self.client_name.setText(settings.client_settings.client_name)
        if self.servers.count() == 0:
            self.reload_servers()

    def closed(self):
        if self.servers_finder_thread:
            self.servers_finder_thread.stop_me()
            self.servers_finder_thread.wait()


class ServersFinderThread(QThread):
    server_found = Signal(object)
    text_changed = Signal(str)

    TEXT_TEMPLATE = 'Searching interface "%s"...'

    def __init__(self, parent):
        self._stopping = False
        super(ServersFinderThread, self).__init__(parent)

    def run(self):
        from client import find_servers
        prev_interface = None
        for interface, result in find_servers():
            if self._stopping:
                break
            if interface != prev_interface:
                self.text_changed.emit(self.TEXT_TEMPLATE % interface)
                prev_interface = interface
                print interface
            if result:
                self.server_found.emit(result)

    def stop_me(self):
        self._stopping = True
