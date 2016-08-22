VID = 0x1B4F
PID = 0x9206


def find_arduino_port():
    from serial.tools.list_ports import comports
    for port in comports():
        if port.pid == PID and port.vid == VID:
            return port.device


def send_code(code, port=None):
    from serial import Serial
    port = port or find_arduino_port()
    serial = Serial(port)
    return serial


