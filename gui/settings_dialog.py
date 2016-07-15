from PySide.QtGui import *
from PySide.QtCore import *
from settings import Settings
from consts import *

settings = Settings()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
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
    STOP_LOADING_SERVERS_TEXT = "Stop"

    def __init__(self, parent=None):
        super(ClientSettings, self).__init__(title="Client Settings", parent=parent)
        layout = QFormLayout()
        self.client_name = QLineEdit(parent=self)
        layout.addRow("Client Name", self.client_name)
        current_server_row = QWidget(parent=self)
        current_server_row.setLayout(QHBoxLayout())
        self.current_server = QLabel("Hello World", parent=current_server_row)
        self.current_server_disconnect = QPushButton('Disconnect', parent=current_server_row)
        current_server_row.layout().addWidget(self.current_server)
        current_server_row.layout().addWidget(self.current_server_disconnect)
        current_server_row.setVisible(False)
        layout.addRow(current_server_row)
        # Setup servers search
        self.servers = QListWidget(self)
        layout.addRow(self.servers)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setHidden(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        layout.addRow(self.progress_bar)
        self.reload_servers_button = QPushButton(self.LOAD_SERVERS_TEXT)
        self.reload_servers_button.clicked.connect(self.reload_servers)
        layout.addRow(self.reload_servers_button)
        self.setLayout(layout)
        self.servers_finder_thread = None

    def reload_servers(self):
        # First, empty the list
        if self.servers_finder_thread is None:
            self.servers.clear()
            self.servers_finder_thread = ServersFinderThread(self)
            self.servers_finder_thread.server_found.connect(self.server_found)
            self.servers_finder_thread.started.connect(lambda: self.progress_bar.setVisible(True))
            self.servers_finder_thread.finished.connect(self.server_search_finished)
            self.reload_servers_button.setText(self.STOP_LOADING_SERVERS_TEXT)
            self.servers_finder_thread.start()
        else:
            self.servers_finder_thread.stop_me()

    def server_found(self, server_info):
        server_name, ip_address, port = server_info
        item = QListWidgetItem("{} ({}:{})".format(server_name, ip_address, port), view=self.servers)
        item.setData(Qt.UserRole, (server_name, port, ip_address))

    def server_search_finished(self):
        self.progress_bar.setVisible(False)
        del self.servers_finder_thread
        self.servers_finder_thread = None
        self.reload_servers_button.setText(self.LOAD_SERVERS_TEXT)

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

    def __init__(self, parent):
        self._stopping = False
        super(ServersFinderThread, self).__init__(parent)

    def run(self):
        from client import find_servers
        for result in find_servers():
            if self._stopping:
                break
            if result:
                self.server_found.emit(result)

    def stop_me(self):
        self._stopping = True
