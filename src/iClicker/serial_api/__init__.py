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
CODE_CUSTOM_CLICK = 10
CODE_MOVE_CLICKER = 11
CODE_RESET_CLICKER = 12


VID = 0x1B4F
PID = 0x9206


class Clicker(object):
    @classmethod
    def find_clicker_port(cls):
        from serial.tools.list_ports import comports
        for port in comports():
            if port.pid == PID and port.vid == VID:
                return port.device

    @contextmanager
    def _serial_interaction(self, code):
        from time import sleep

        from serial import Serial, SerialException
        port = self.port or self.find_clicker_port()
        serial = None
        a = 0
        while not serial and a < 10:
            try:
                serial = Serial(port)
            except SerialException:
                sleep(1)
                a += 1
        if not serial:
            raise SerialException("Couldn't connect to the clicker at port {}".format(port))
        serial.write(str(code) + '\n')
        yield serial
        serial.close()

    def _send_code(self, code):
        with self._serial_interaction(code):
            pass

    def _send_data(self, code, *data):
        with self._serial_interaction(code) as serial:
            for obj in data:
                serial.write(str(obj) + '\n')

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
    def click_pos(self, angle):
        self._send_data(CODE_SET_CLICK_POS, angle)

    @click2_pos.setter
    def click2_pos(self, angle):
        self._send_data(CODE_SET_CLICK2_POS, angle)

    @released_pos.setter
    def released_pos(self, angle):
        self._send_data(CODE_SET_RELEASED_POS, angle)

    def click(self):
        self._send_code(CODE_CLICK)

    def click2(self):
        self._send_code(CODE_CLICK2)

    def custom_click(self, click_angle, release_angle):
        self._send_data(CODE_CUSTOM_CLICK, click_angle, release_angle)

    def move_to(self, angle):
        self._send_data(CODE_MOVE_CLICKER, angle)

    def move_to_released_pos(self):
        self._send_code(CODE_RESET_CLICKER)

    def is_click2_enabled(self):
        return 0 <= self.click2_pos <= 180

    def disable_click2(self):
        self.click2_pos = 255

    def __init__(self, port=None):
            self.port = port
