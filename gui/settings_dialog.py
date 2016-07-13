from PySide.QtGui import *
from PySide.QtCore import Qt
from utils import Settings
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
        self.settings_groups.currentChanged.connect(self.mode_changed)

        mode_container = QWidget(self)
        mode_container.setLayout(QFormLayout())
        mode_container.layout().addRow("Mode: ", self.mode)
        layout.addWidget(mode_container)
        layout.addWidget(self.settings_groups)

        self.buttons_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Apply | QDialogButtonBox.Cancel,
                                            parent=self)
        self.buttons_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.buttons_box)

        self.setLayout(layout)

        self.mode.setCurrentIndex(self.mode.findText(settings.mode))

    def mode_changed(self, new_index):
        print new_index
        mode = self.settings_groups.widget(new_index)
        print mode


class ServerSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(title="Server Settings", parent=parent)
        layout = QFormLayout()
        self.server_name = QLineEdit(settings.identifier_name, parent=self)
        self.server_port = QSpinBox(parent=self)
        self.server_port.setMaximum(65535)
        self.server_port.setValue(settings.server_port)
        layout.addRow("Server Name:", self.server_name)
        layout.addRow("Server Port:", self.server_port)
        layout.addRow(QPushButton('Calibrate Clicker', parent=self))
        self.setLayout(layout)


class ClientSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ClientSettings, self).__init__(title="Client Settings", parent=parent)
        layout = QFormLayout()
        self.client_name = QLineEdit(settings.identifier_name, parent=self)
        layout.addRow("Client Name", self.client_name)
        self.servers = QListWidget(self)
        layout.addRow(self.servers)
        reload_servers = QPushButton("Re/Load Servers")
        reload_servers.clicked.connect(self.reload_servers)
        layout.addRow(reload_servers)
        self.setLayout(layout)
        # self.reload_servers()

    def reload_servers(self):
        # First, empty the list
        self.servers.clear()
        from client import find_servers
        for server_name, port, ip_address in find_servers():
            item = QListWidgetItem("{} ({}:{})".format(server_name, ip_address, port), view=self.servers)
            item.setData(Qt.UserRole, (server_name, port, ip_address))
