from PySide.QtGui import *
from utils import Settings

settings = Settings()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle('Mazgan Settings')
        layout = QVBoxLayout()
        self.mode = QComboBox(self)
        self.mode.addItems(['Server', 'Client'])

        self.settings_groups = QStackedWidget(self)
        self.settings_groups.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_groups.addWidget(ServerSettings(self))
        self.settings_groups.addWidget(ClientSettings(self))

        self.mode.currentIndexChanged.connect(self.settings_groups.setCurrentIndex)

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


class ServerSettings(QGroupBox):
    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(title="Server Settings", parent=parent)
        layout = QFormLayout()
        self.server_name = QLineEdit(settings.server_name, parent=self)
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
        self.server_name = QLineEdit(settings.server_name, parent=self)
        layout.addRow("Client Name", self.server_name)
        self.setLayout(layout)
