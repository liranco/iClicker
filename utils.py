import os
from PySide.QtCore import QSettings

from consts import *


class Settings(QSettings):
    _singleton_object = None

    def __new__(cls):
        if cls._singleton_object is None:
            instance = QSettings.__new__(cls)
            Settings.__init__(instance)
            cls._singleton_object = instance
        return cls._singleton_object

    def __init__(self):
        if Settings._singleton_object is self:
            return
        super(Settings, self).__init__(os.path.join(os.path.dirname(__file__), SETTINGS_FILE), QSettings.IniFormat)
        self.setFallbacksEnabled(False)

    @property
    def server_name(self):
        return self.value("server_name", "New Server")

    @server_name.setter
    def server_name(self, value):
        self.setValue("server_name", value)

    @property
    def client_name(self):
        import platform
        return self.value("client_name", platform.node())

    @client_name.setter
    def client_name(self, value):
        self.setValue("client_name", value)

    @property
    def server_port(self):
        return self.value("server_port", DEFAULT_SERVER_PORT)

    @server_port.setter
    def server_port(self, value):
        self.setValue("server_port", value)

    @property
    def mode(self):
        return self.value("run_mode", CLIENT_MODE)

    @mode.setter
    def mode(self, value):
        self.setValue("run_mode", value)
