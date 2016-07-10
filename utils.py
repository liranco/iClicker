import os
from PySide.QtCore import QSettings
from PySide.QtGui import QDialog, QFormLayout

from consts import *


def singleton(cls):
    """
    http://stackoverflow.com/questions/674304
    """
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance


# @singleton
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
        return self.value("server_name")

    @server_name.setter
    def server_name(self, value):
        self.setValue("server_name", value)

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
