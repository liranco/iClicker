from contextlib import contextmanager

CODE_GET_CLICK_POS = 1
CODE_SET_CLICK_POS = 2
CODE_GET_RELEASED_POS = 3
CODE_SET_RELEASED_POS = 4
CODE_GET_CLICK2_POS = 5
CODE_SET_CLICK2_POS = 6
CODE_GET_TEMPERATURE = 7
CODE_CLICK = 8
CODE_CLICK2 = 9
CODE_MOVE_CLICKER = 10
CODE_RESET_CLICKER = 11


VID = 0x1B4F
PID = 0x9206


class Arduino(object):
    @classmethod
    def find_arduino_port(cls):
        from serial.tools.list_ports import comports
        for port in comports():
            if port.pid == PID and port.vid == VID:
                return port.device

    @contextmanager
    def _serial_interaction(self, code):
        from serial import Serial
        port = self.port or self.find_arduino_port()
        serial = Serial(port)
        serial.write(str(code) + '\n')
        yield serial
        serial.close()

    def _send_code(self, code):
        with self._serial_interaction(code):
            pass

    def _send_data(self, code, data):
        with self._serial_interaction(code) as serial:
            serial.write(str(data) + '\n')

    def _get_data(self, code):
        with self._serial_interaction(code) as serial:
            data = serial.readline()
        return data

    @property
    def temperature(self):
        return float(self._get_data(CODE_GET_TEMPERATURE))

    @property
    def click_pos(self):
        return int(self._get_data(CODE_GET_CLICK_POS))

    @property
    def click2_pos(self):
        return int(self._get_data(CODE_GET_CLICK2_POS))

    @property
    def released_pos(self):
        return int(self._get_data(CODE_GET_RELEASED_POS))

    @click_pos.setter
    def click_pos(self, value):
        self._send_data(CODE_SET_CLICK_POS, value)

    @click2_pos.setter
    def click2_pos(self, value):
        self._send_data(CODE_SET_CLICK2_POS, value)

    @released_pos.setter
    def released_pos(self, value):
        self._send_data(CODE_SET_RELEASED_POS, value)

    def click(self):
        self._send_code(CODE_CLICK)

    def click2(self):
        self._send_code(CODE_CLICK2)

    def move_to(self, value):
        self._send_data(CODE_MOVE_CLICKER, value)

    def move_to_released_pos(self):
        self._send_code(CODE_RESET_CLICKER)

    def is_click2_enabled(self):
        return self.click2_pos == 255

    def disable_click2(self):
        self.click2_pos = 255

    def __init__(self, port=None):
            self.port = port
