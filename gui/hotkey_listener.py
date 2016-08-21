import ctypes
import win32con
from ctypes import wintypes
from PySide.QtCore import *
from settings import BaseSettingsGroup

HOTKEY_ID = 9119


class HotkeySettings(BaseSettingsGroup):
    @property
    def is_enabled(self):
        value = self.value('is_enabled', default=False)
        return value.lower() == 'true' if isinstance(value, basestring) else value

    @is_enabled.setter
    def is_enabled(self, value):
        self.set_value('is_enabled', bool(value))

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

    def __init__(self, parent=None):
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

    def run(self):

        # Solution taken from: http://timgolden.me.uk/python/win32_how_do_i/catch_system_wide_hotkeys.html
        user32 = ctypes.windll.user32
        by_ref = ctypes.byref

        if not user32.RegisterHotKey(None, HOTKEY_ID, self._modifiers, self._key):
            raise WindowsError("Unable to register id", HOTKEY_ID)

        try:
            msg = wintypes.MSG()
            while user32.GetMessageA(by_ref(msg), None, 0, 0) != 0:
                if msg.message == win32con.WM_HOTKEY:
                    if msg.wParam == HOTKEY_ID:
                        self.hotkey_hit.emit()

                user32.TranslateMessage(by_ref(msg))
                user32.DispatchMessageA(by_ref(msg))

        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)
