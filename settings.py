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

        self.server_settings = ServerSettings(self)
        self.client_settings = ClientSettings(self)

    @property
    def mode(self):
        return self.value("run_mode", CLIENT_MODE)

    @mode.setter
    def mode(self, value):
        self.setValue("run_mode", value)


class ServerSettings(object):
    def __init__(self, settings):
        self._settings = settings         # type: Settings
        self.value = settings.value
        self.setValue = settings.setValue

    @property
    def server_name(self):
        return self.value("server_name", "New Server")

    @server_name.setter
    def server_name(self, value):
        self.setValue("server_name", value)

    @property
    def server_password(self):
        sha1, password_length = self.value("server_password", [None, 0])
        return sha1, int(password_length)

    @server_password.setter
    def server_password(self, value):
        from hashlib import sha1
        self.setValue("server_password", (sha1(value).hexdigest(), len(value)))

    @property
    def server_port(self):
        return self.value("server_port", DEFAULT_SERVER_PORT)

    @server_port.setter
    def server_port(self, value):
        self.setValue("server_port", value)


class ClientSettings(object):
    def __init__(self, settings):
        self._settings = settings         # type: Settings
        self.value = settings.value
        self.setValue = settings.setValue

    @property
    def client_name(self):
        import platform
        return self.value("client_name", platform.node())

    @client_name.setter
    def client_name(self, value):
        self.setValue("client_name", value)

    @property
    def connected_server(self):
        return self.value('connected_server', None)

    @connected_server.setter
    def connected_server(self, value):
        server_name, server_ip, port = value
        self.setValue(server_name, server_ip, port)
