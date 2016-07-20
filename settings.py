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
        self.setIniCodec('UTF-8')
        self.setFallbacksEnabled(False)

        self.server_settings = ServerSettings(self)
        self.client_settings = ClientSettings(self)

    @property
    def mode(self):
        return self.value("run_mode", CLIENT_MODE).capitalize()

    @mode.setter
    def mode(self, value):
        self.setValue("run_mode", value)

    def setValue(self, *args, **kwargs):
        QSettings.setValue(self, *args, **kwargs)
        self.sync()

    def value(self, *args, **kwargs):
        self.sync()
        return QSettings.value(self, *args, **kwargs)


class BaseSettingsGroup(object):
    def __init__(self, settings):
        self._settings = settings         # type: Settings

    @property
    def server_password(self):
        sha1, _ = self.value("server_password", [None, 0])
        return sha1

    @property
    def server_password_length(self):
        _, password_length = self.value("server_password", [None, 0])
        return int(password_length)

    @server_password.setter
    def server_password(self, value):
        from hashlib import sha1
        self.set_value("server_password", (sha1(value).hexdigest(), len(value)))

    def value(self, value_name, default=None):
        self._settings.beginGroup(type(self).__name__)
        value = self._settings.value(value_name, default)
        self._settings.endGroup()
        return value

    def set_value(self, value_name, value):
        self._settings.beginGroup(type(self).__name__)
        self._settings.setValue(value_name, value)
        self._settings.endGroup()


class ServerSettings(BaseSettingsGroup):

    @property
    def server_name(self):
        return self.value("server_name", "New Server")

    @server_name.setter
    def server_name(self, value):
        self.set_value("server_name", value)

    @property
    def server_port(self):
        return int(self.value("server_port", DEFAULT_SERVER_PORT))

    @server_port.setter
    def server_port(self, value):
        self.set_value("server_port", value)


class ClientSettings(BaseSettingsGroup):
    @property
    def client_name(self):
        import platform
        return self.value("client_name", platform.node())

    @client_name.setter
    def client_name(self, value):
        self.set_value("client_name", value)

    @property
    def connected_server(self):
        connected_server = self.value('connected_server', None)
        if connected_server:
            server_name, server_ip, port = connected_server
            return server_name, server_ip, int(port)
        return None

    @connected_server.setter
    def connected_server(self, value):
        if value:
            server_name, server_ip, port = value
            self.set_value("connected_server", (server_name, server_ip, port))
        else:
            self.set_value("connected_server", None)
