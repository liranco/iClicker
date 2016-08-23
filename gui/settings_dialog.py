from PySide.QtGui import *
from PySide.QtCore import *
from settings import Settings, ServerSettings, ClientSettings
from notification_widget import NotificationSettings
from hotkey_listener import HotkeySettings
from consts import *

settings = Settings()
server_settings = ServerSettings()
client_settings = ClientSettings()
notification_settings = NotificationSettings()
hotkey_settings = HotkeySettings()


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle('Mazgan Settings')
        self.setWindowFlags(Qt.Window)
        layout = QVBoxLayout()
        self.current_mode = None
        self.mode = QComboBox(self)
        self.mode.addItems((CLIENT_MODE, SERVER_MODE))

        self.settings_groups = QStackedWidget(self)
        self.settings_groups.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.settings_groups.addWidget(ClientSettings(self))
        self.settings_groups.addWidget(ServerSettings(self))

        self.mode.currentIndexChanged.connect(self.mode_changed)

        mode_container = QWidget(self)
        mode_container.setLayout(QFormLayout())
        mode_container.layout().addRow("Select Your &Mode: ", self.mode)
        layout.addWidget(mode_container)
        layout.addWidget(self.settings_groups)
        self.notification_settings = NotificationSettings(self)
        layout.addWidget(self.notification_settings)

        self.hotkey_settings = HotKeySettingsGroup(self)
        layout.addWidget(self.hotkey_settings)

        self.buttons_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply,
                                            parent=self)
        self._is_apply_clicked = False
        self.buttons_box.button(QDialogButtonBox.Ok).clicked.connect(self.ok_button_clicked)
        self.buttons_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.buttons_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_button_clicked)

        self.buttons_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.buttons_box)

        self.setLayout(layout)

        required_mode_index = self.mode.findText(settings.mode)
        if self.mode.currentIndex() != required_mode_index:
            self.mode.setCurrentIndex(required_mode_index)
        else:
            # Because the index hasn't really changed but the mode_changed function still needs to be called.
            self.mode_changed(required_mode_index)

    def mode_changed(self, new_mode_index):
        if self.current_mode:
            self.current_mode.closed()
        self.settings_groups.setCurrentIndex(new_mode_index)
        new_mode = self.settings_groups.currentWidget()
        new_mode.activated()
        self.current_mode = new_mode

    def all_settings(self):
        """
        :rtype: list[BaseSettings]
        """
        return [self.settings_groups.widget(i) for i in xrange(self.settings_groups.count())] + \
               [self.notification_settings, self.hotkey_settings]

    def closeEvent(self, event):
        [widget.closed() for widget in self.all_settings()]

    def ok_button_clicked(self):
        self.apply_button_clicked()
        self.close()

    def apply_button_clicked(self):
        settings.mode = self.mode.currentText()
        [widget.save() for widget in self.all_settings()]
        self._is_apply_clicked = True

    def exec_(self):
        super(SettingsDialog, self).exec_()
        if self._is_apply_clicked:
            return self.mode.currentText()


class BaseSettings(QGroupBox):
    def closed(self):
        pass

    def save(self):
        pass


class BaseModeSettings(BaseSettings):
    def make_password_field(self):
        server_password = QLineEdit(parent=self)
        server_password.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        server_password.is_changed = False
        server_password.textChanged.connect(self.password_changed)
        return server_password

    def password_changed(self):
        self.server_password.is_changed = True

    def activated(self):
        pass


class ServerSettings(BaseModeSettings):
    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(title="Server Settings", parent=parent)
        layout = QFormLayout()
        self.server_name = QLineEdit(parent=self)
        self.server_port = QSpinBox(parent=self)
        self.server_port.setMaximum(65535)
        self.server_password = self.make_password_field()
        layout.addRow("Server &Name:", self.server_name)
        layout.addRow("Server &Port:", self.server_port)
        layout.addRow("P&assword:", self.server_password)
        calibrate_button = QPushButton('&Calibrate Clicker', parent=self)
        calibrate_button.clicked.connect(lambda: ClickerCalibrator(self).exec_())
        layout.addRow(calibrate_button)
        self.setLayout(layout)

        self.server_name.setText(server_settings.server_name)
        self.server_port.setValue(server_settings.server_port)
        self.server_password.setText('x' * server_settings.server_password_length)
        self.server_password.is_changed = False

    def save(self):
        server_settings.server_name = self.server_name.text()
        server_settings.server_port = self.server_port.value()
        if self.server_password.is_changed:
            server_settings.server_password = self.server_password.text()


class ClientSettings(BaseModeSettings):
    LOAD_SERVERS_TEXT = "&Load Servers"
    STOP_LOADING_SERVERS_TEXT = "Click to Stop."

    def __init__(self, parent=None):
        super(ClientSettings, self).__init__(title="Client Settings", parent=parent)
        layout = QFormLayout()
        self.client_name = QLineEdit(parent=self)
        layout.addRow("Client &Name", self.client_name)
        current_server_row = QWidget(parent=self)
        current_server_row.setLayout(QHBoxLayout())
        current_server_row.layout().setContentsMargins(0, 0, 0, 0)
        self.current_server_ip = QLineEdit(parent=current_server_row)
        self.current_server_ip.setPlaceholderText("&IP Address")
        self.current_server_port = QSpinBox(parent=current_server_row)
        self.current_server_port.setMaximum(65535)
        self.current_server_name = None
        self.server_password = self.make_password_field()
        current_server_row.layout().addWidget(self.current_server_ip)
        current_server_row.layout().addWidget(self.current_server_port)
        layout.addRow("Current Server:", current_server_row)
        layout.addRow("Server P&assword:", self.server_password)
        # Setup servers search
        self.servers = QListWidget(self)
        self.servers.currentItemChanged.connect(self.server_picked_from_list)
        layout.addRow('&Pick a server:', self.servers)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setHidden(True)
        layout.addRow(self.progress_bar)
        self.reload_servers_button = QPushButton(self.LOAD_SERVERS_TEXT)
        self.reload_servers_button.clicked.connect(self.reload_servers)
        layout.addRow(self.reload_servers_button)
        self.setLayout(layout)
        self.servers_finder_thread = None

        self.client_name.setText(client_settings.client_name)
        current_server = client_settings.connected_server
        if current_server:
            name, ip, port = current_server
            self.current_server_name = name
            self.current_server_ip.setText(ip)
            self.current_server_port.setValue(port)
        self.server_password.setText('x' * client_settings.server_password_length)
        self.server_password.is_changed = False

    def reload_servers(self):
        # First, empty the list
        if self.servers_finder_thread is None:
            self.servers.clear()
            self.servers_finder_thread = ServersFinderThread(self)
            self.servers_finder_thread.server_found.connect(self.server_search_found_item)
            self.servers_finder_thread.text_changed.connect(
                lambda text: self.reload_servers_button.setText("%s %s" % (text, self.STOP_LOADING_SERVERS_TEXT)))
            self.servers_finder_thread.started.connect(self.server_search_started)
            self.servers_finder_thread.finished.connect(self.server_search_finished)
            self.servers_finder_thread.start()
        else:
            self.servers_finder_thread.stop_me()

    def server_search_started(self):
        self.progress_bar.setVisible(True)
        self.reload_servers_button.setText(self.STOP_LOADING_SERVERS_TEXT)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)

    def server_search_found_item(self, server_info):
        server_name, ip_address, port = server_info
        item = QListWidgetItem(u"{} ({}:{})".format(server_name, ip_address, port), view=self.servers)
        item.setData(Qt.UserRole, (server_name, ip_address, port))

    def server_search_finished(self):
        self.progress_bar.setVisible(False)
        del self.servers_finder_thread
        self.servers_finder_thread = None
        self.reload_servers_button.setText(self.LOAD_SERVERS_TEXT)

    def server_picked_from_list(self, item):
        if item is None:
            return
        server_name, ip_address, port = item.data(Qt.UserRole)
        self.current_server_ip.setText(ip_address)
        self.current_server_port.setValue(port)
        self.current_server_name = server_name

    def activated(self):
        if self.servers.count() == 0:
            self.reload_servers()

    def closed(self):
        if self.servers_finder_thread:
            self.servers_finder_thread.stop_me()
            self.servers_finder_thread.wait()
            self.servers.clear()

    def save(self):
        client_settings.client_name = self.client_name.text()
        if self.current_server_ip.text() == '' or self.current_server_port.value() == 0:
            client_settings.connected_server = None
        else:
            client_settings.connected_server = (self.current_server_name,
                                                self.current_server_ip.text(),
                                                self.current_server_port.value())
        if self.server_password.is_changed:
            client_settings.server_password = self.server_password.text()


class ServersFinderThread(QThread):
    server_found = Signal(object)
    text_changed = Signal(str)

    TEXT_TEMPLATE = 'Searching interface "%s"...'

    def __init__(self, parent):
        self._stopping = False
        super(ServersFinderThread, self).__init__(parent)

    def run(self):
        from client import find_servers
        prev_interface = None
        for interface, result in find_servers():
            if self._stopping:
                break
            if interface != prev_interface:
                self.text_changed.emit(self.TEXT_TEMPLATE % interface)
                prev_interface = interface
            if result:
                self.server_found.emit(result)

    def stop_me(self):
        self._stopping = True


class NotificationSettings(BaseSettings):
    def __init__(self, parent=None):
        super(NotificationSettings, self).__init__(title='Notification Settings', parent=parent)
        layout = QFormLayout()
        color_widgets = QWidget(self)
        color_widgets.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        color_widgets.setLayout(QHBoxLayout())
        color_widgets.layout().setContentsMargins(0, 0, 0, 0)

        self.color_display = QLabel()
        self.color_display.setFixedSize(16, 16)
        self._set_color()
        self.color_display.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        color_widgets.layout().addWidget(self.color_display)
        color_pick_button = QPushButton('&Set')
        color_pick_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        color_pick_button.clicked.connect(self._get_color)
        color_widgets.layout().addWidget(color_pick_button)
        layout.addRow('Notification Color:', color_widgets)

        notification_duration_row = QWidget()
        notification_duration_row.setLayout(QHBoxLayout())
        notification_duration_row.layout().setContentsMargins(0, 0, 0, 0)
        self.notification_duration = QSpinBox(self)
        self.notification_duration.setMinimum(1)
        self.notification_duration.setValue(notification_settings.duration)
        self.notification_duration.setSuffix(' seconds')
        notification_duration_row.layout().addWidget(self.notification_duration)
        self.notification_expires = QCheckBox('Stay &Until Closed', self)
        self.notification_expires.setChecked(notification_settings.notification_expires)
        notification_duration_row.layout().addWidget(self.notification_expires)

        layout.addRow('Notification &Duration:', notification_duration_row)
        self.setLayout(layout)

    def _set_color(self, color=None):
        color = color or notification_settings.color
        r, g, b = color.toTuple()[:3]
        self.color_display.setStyleSheet('QWidget { background-color: #%.2x%.2x%.2x; border: none; }' % (r, g, b))
        self._selected_color = color

    def _get_color(self):
        dialog = QColorDialog(notification_settings.color, self)
        dialog.exec_()
        color = dialog.selectedColor()
        if color.isValid():
            self._set_color()

    def save(self):
        notification_settings.color = self._selected_color
        notification_settings.duration = self.notification_duration.value()
        notification_settings.notification_expires = self.notification_expires.isChecked()


class HotKeySettingsGroup(BaseSettings):
    def __init__(self, parent=None):
        super(HotKeySettingsGroup, self).__init__(title='Global Hotkey', parent=parent)
        layout = QVBoxLayout()
        self._key = hotkey_settings.key
        self.is_enabled = QCheckBox('Enable?')
        self.ctrl_mod = QCheckBox('Ctrl')
        self.alt_mod = QCheckBox('Alt')
        self.win_mod = QCheckBox('Win')
        self.key_input = QLineEdit()
        self.key_input.keyPressEvent = self.line_key_press_event

        hotkey_options = QWidget()
        hotkey_options.setLayout(QHBoxLayout())
        hotkey_options.layout().setContentsMargins(0, 0, 0, 0)
        map(hotkey_options.layout().addWidget, (self.ctrl_mod, self.alt_mod, self.win_mod, QLabel('+'), self.key_input))
        layout.addWidget(self.is_enabled)
        layout.addWidget(hotkey_options)

        self.setLayout(layout)

        self.is_enabled.setChecked(hotkey_settings.is_enabled)
        self.ctrl_mod.setChecked(hotkey_settings.ctrl)
        self.alt_mod.setChecked(hotkey_settings.alt)
        self.win_mod.setChecked(hotkey_settings.win)
        if hotkey_settings.key_text:
            self.key_input.setText(hotkey_settings.key_text)

    def line_key_press_event(self, event):
        if event.key() not in (0, Qt.Key_unknown):
            try:
                self.key_input.setText(str(QKeySequence(event.key()).toString()))
                self._key = event.nativeVirtualKey()
            except UnicodeEncodeError:
                return

    def save(self):
        hotkey_settings.is_enabled = self.is_enabled.isChecked()
        hotkey_settings.ctrl = self.ctrl_mod.isChecked()
        hotkey_settings.alt = self.alt_mod.isChecked()
        hotkey_settings.win = self.win_mod.isChecked()
        hotkey_settings.key = self._key
        hotkey_settings.key_text = self.key_input.text()


class ClickerCalibrator(QDialog):
    def __init__(self, parent):
        from serial_api import Arduino
        super(ClickerCalibrator, self).__init__(parent)
        layout = QFormLayout()

        self.arduino = Arduino()

        def get_spin_box_widget():
            widget = QWidget(self)
            widget.setLayout(QHBoxLayout())
            widget.layout().setContentsMargins(0, 0, 0, 0)
            spin_box = QSpinBox(widget)
            spin_box.setMinimum(0)
            spin_box.setMaximum(180)
            spin_box.setSuffix(u'\u00B0')
            widget.layout().addWidget(spin_box)
            test_button = QPushButton('Test', widget)
            test_button.clicked.connect(lambda: self.test_value(spin_box.value()))
            widget.layout().addWidget(test_button)
            widget.spin_box = spin_box
            widget.setEnabled = lambda enabled: [val.setEnabled(enabled) for val in (spin_box, test_button)]
            return widget

        self.is_switch_on_off = QCheckBox("Does the switch has two buttons (On/Off)?")
        layout.addRow(self.is_switch_on_off)
        warn_label = QLabel("Be careful with the values you enter! If you'll enter a value too large or too low, "
                            "the clicker may break!")
        warn_label.setStyleSheet('QLabel { color: red }')
        layout.addRow(warn_label)
        self.switch_off_position = get_spin_box_widget()
        layout.addRow("Click Off Position", self.switch_off_position)
        self.is_switch_on_off.stateChanged.connect(
            lambda: self.switch_off_position.setEnabled(self.is_switch_on_off.isChecked()))
        self.neutral_position = get_spin_box_widget()
        layout.addRow("Neutral Position", self.neutral_position)
        self.switch_on_position = get_spin_box_widget()
        layout.addRow("Click Position", self.switch_on_position)

        self.buttons_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self)
        self.buttons_box.button(QDialogButtonBox.Save).clicked.connect(self.save)
        self.buttons_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        layout.addRow(self.buttons_box)

        self.setLayout(layout)

        self.fill_values()

    def test_value(self, new_value):
        print new_value, type(new_value)
        self.arduino.move_to(new_value)

    def fill_values(self):
        is_switch_on_off = self.arduino.is_click2_enabled()
        released_value = self.arduino.released_pos
        self.is_switch_on_off.setChecked(is_switch_on_off)
        if is_switch_on_off:
            self.switch_off_position.spin_box.setValue(self.arduino.click2_pos)
            self.switch_off_position.setEnabled(True)
        else:
            self.switch_off_position.spin_box.setValue(released_value)
            self.switch_off_position.setEnabled(False)
        self.neutral_position.spin_box.setValue(released_value)
        self.switch_on_position.spin_box.setValue(self.arduino.click_pos)

    def save(self):
        if self.is_switch_on_off.isChecked():
            self.arduino.click2_pos = self.switch_off_position.spin_box.value()
        else:
            self.arduino.disable_click2()
        self.arduino.click_pos = self.switch_on_position.spin_box.value()
        self.arduino.released_pos = self.neutral_position.spin_box.value()
        self.close()

    def close(self):
        self.arduino.move_to_released_pos()
        super(ClickerCalibrator, self).close()
