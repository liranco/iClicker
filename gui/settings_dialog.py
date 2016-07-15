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

        self.mode.currentIndexChanged.connect(self.settings_groups.setCurrentIndex)

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


class ServerSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(title="Server Settings", parent=parent)
        layout = QFormLayout()
        self.server_name = QLineEdit(settings.server_name, parent=self)
        self.server_port = QSpinBox(parent=self)
        self.server_port.setMaximum(65535)
        self.server_port.setValue(settings.server_port)
        self.server_password = QLineEdit('x' * settings.server_password[1], parent=self)
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


class ClientSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ClientSettings, self).__init__(title="Client Settings", parent=parent)
        layout = QFormLayout()
        self.client_name = QLineEdit(settings.client_name, parent=self)
        layout.addRow("Client Name", self.client_name)
        self.servers = QListWidget(self)
        layout.addRow(self.servers)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setHidden(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        layout.addRow(self.progress_bar)
        self.reload_servers_button = QPushButton("Re/Load Servers")
        self.reload_servers_button.clicked.connect(self.reload_servers)
        layout.addRow(self.reload_servers_button)
        self.setLayout(layout)
        self.servers_finder_thread = None
        self.reload_servers()

    def reload_servers(self):
        # First, empty the list
        self.servers.clear()
        if self.servers_finder_thread is None:
            self.servers_finder_thread = ServersFinderThread(self)
            self.servers_finder_thread.server_found.connect(self.server_found)
            self.servers_finder_thread.started.connect(lambda: self.progress_bar.setVisible(True))
            self.servers_finder_thread.finished.connect(self.server_search_finished)
            self.reload_servers_button.setEnabled(False)
            self.servers_finder_thread.start()

    def server_found(self, server_info):
        server_name, ip_address, port = server_info
        item = QListWidgetItem("{} ({}:{})".format(server_name, ip_address, port), view=self.servers)
        item.setData(Qt.UserRole, (server_name, port, ip_address))

    def server_search_finished(self):
        self.progress_bar.setVisible(False)
        del self.servers_finder_thread
        self.servers_finder_thread = None
        self.reload_servers_button.setEnabled(True)


class ServersFinderThread(QThread):
    server_found = Signal(object)

    def run(self):
        from client import find_servers
        for result in find_servers():
            self.server_found.emit(result)
