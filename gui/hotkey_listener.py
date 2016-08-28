import ctypes
import win32con
import win32gui
from PySide.QtCore import *
from settings import BaseSettingsGroup

HOTKEY_ID = 9119
user32 = ctypes.windll.user32


class HotkeySettings(BaseSettingsGroup):
    @property
    def is_enabled(self):
        return any((self.alt, self.ctrl, self.win, self.key))

    @property
    def alt(self):
        value = self.value('alt', default=False)
        return value.lower() == 'true' if isinstance(value, basestring) else value

    @alt.setter
    def alt(self, value):
        self.set_value('alt', bool(value))

    @property
    def ctrl(self):
        value = self.value('ctrl', default=False)
        return value.lower() == 'true' if isinstance(value, basestring) else value

    @ctrl.setter
    def ctrl(self, value):
        self.set_value('ctrl', bool(value))

    @property
    def win(self):
        value = self.value('win', default=False)
        return value.lower() == 'true' if isinstance(value, basestring) else value

    @win.setter
    def win(self, value):
        self.set_value('win', bool(value))

    @property
    def key(self):
        value = self.value('key', default=None)
        if isinstance(value, type(None)):
            return value
        return int(value)

    @key.setter
    def key(self, value):
        self.set_value('key', value)

    @property
    def key_text(self):
        value = self.value('key_text', default=None)
        if isinstance(value, type(None)):
            return value
        return str(value)

    @key_text.setter
    def key_text(self, value):
        self.set_value('key_text', value)


class HotkeyThread(QThread):
    hotkey_hit = Signal()

    def __init__(self, parent):
        super(HotkeyThread, self).__init__(parent)
        modifier = 0
        settings = HotkeySettings()
        if settings.win:
            modifier |= win32con.MOD_WIN
        if settings.alt:
            modifier |= win32con.MOD_ALT
        if settings.ctrl:
            modifier |= win32con.MOD_CONTROL
        self._modifiers = modifier
        self._key = settings.key
        self._stop_run = False

    def run(self):

        # Solution taken from: http://timgolden.me.uk/python/win32_how_do_i/catch_system_wide_hotkeys.html
        if not user32.RegisterHotKey(None, HOTKEY_ID, self._modifiers, self._key):
            raise WindowsError("Unable to register id")
        try:
            while True:
                user32.MsgWaitForMultipleObjects(0, None, False, 10, win32con.QS_HOTKEY)
                if self._stop_run:
                    break
                status, msg = win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
                if status != 0:
                    _, message_type, w_param, _, _, _ = msg
                    if message_type == win32con.WM_HOTKEY:
                        if w_param == HOTKEY_ID:
                            self.hotkey_hit.emit()
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self):
        user32.UnregisterHotKey(None, HOTKEY_ID)
        self._stop_run = True
