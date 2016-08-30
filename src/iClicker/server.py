import hashlib
import hmac
import json
import time
from SocketServer import *
from threading import Thread, Event

from consts import *
from settings import ServerSettings


class UDPBroadcastsHandler(DatagramRequestHandler):
    def handle(self):
        data = json.loads(self.rfile.read())
        code = data['code']
        if code == CODE_FIND_SERVER:
            settings = ServerSettings()
            self.wfile.write(json.dumps(dict(server_name=settings.server_name, port=settings.server_port)))


class BaseServerHandler(StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.server = None  # type: MainServer
        StreamRequestHandler.__init__(self, request, client_address, server)

    def setup(self):
        StreamRequestHandler.setup(self)

    def _post(self, code, **kwargs):
        kwargs['code'] = code
        kwargs['name'] = self.server.name
        self.wfile.write(json.dumps(kwargs))

    def _get(self):
        try:
            data = self.request.recv(1024)
        except socket.error as e:
            if e.errno == socket.errno.EWOULDBLOCK:
                return None, None
            raise
        if data:
            data = json.loads(data)
            return data['code'], data
        else:
            return None, None

    def handlers(self):
        """

        :rtype: dict[int, types.FunctionType]
        """
        raise NotImplementedError()

    def handle(self):
        code, data = self._get()
        if code is None:
            return
        if self._challenge_sequence():
            self._post(CODE_CHALLENGE_SUCCESS)
        else:
            self._post(CODE_CHALLENGE_FAILED)
            return
        # Call the relevant handler
        handlers = {CODE_START_COMM: lambda **_: None}
        handlers.update(self.handlers())
        response = handlers[code](**data)
        response = response or {}  # type: dict
        self._post(CODE_SERVER_RESPONSE, **response)

    def _challenge_sequence(self):
        # Start authentication
        password = ServerSettings().server_password
        if not password:
            # No challenge required.
            expected_response = None
            self._post(CODE_CHALLENGE_NOT_REQUIRED)
        else:
            challenge = os.urandom(16).encode('hex')
            password_hash = hashlib.sha1(password).hexdigest()
            expected_response = hmac.new(challenge, password_hash, hashlib.sha1).hexdigest()
            self._post(CODE_CHALLENGE_START, challenge=challenge)
        code, result = self._get()
        assert code == CODE_CHALLENGE_RESPONSE, code
        response = result['response']
        if response != expected_response:
            return False
        else:
            return True


class MainServerHandler(BaseServerHandler):
    def handlers(self):
        return {
            CODE_START_COMM: self.handle_start_comm,
            CODE_SAY_HELLO: self.handle_say_hello,
            CODE_CLICK: self.handle_click,
            CODE_SET_AUTO_CLICKER: self.handle_set_auto_clicker,
            CODE_GET_SERVER_INFO: self.handle_get_server_info,
            CODE_GET_TEMPERATURE: self.handle_get_temperature,
        }

    def _extend_client_timeout(self):
        client_port, old_update_time = self.server.clients[self.client_address[0]]
        self.server.clients[self.client_address[0]] = (client_port, time.time())

    def handle(self):
        if self.client_address[0] in self.server.clients:
            self._extend_client_timeout()
        BaseServerHandler.handle(self)

    def handle_start_comm(self, notifications_server_port=None, **_):
        if notifications_server_port:
            self.server.clients[self.client_address[0]] = (notifications_server_port, None)
            self._extend_client_timeout()

    def handle_say_hello(self, **_):
        return dict(message='Hello from {}'.format(ServerSettings().server_name))

    def handle_click(self, name, **_):
        try:
            self.server.click()
        except NoClickerError as ex:
            self.server.push(CODE_SHOW_NOTIFICATION, title='Error!', message=str(ex))
        else:
            self.server.push(CODE_SHOW_NOTIFICATION, title='Click!', message='{} has sent a click command'.format(name))

    def handle_set_auto_clicker(self, name, interval, **_):
        assert isinstance(interval, (int, type(None)))
        if isinstance(interval, int) and interval <= 0:
            interval = None
        self.server.set_auto_clicker(interval)
        if interval:
            self.server.push(CODE_SHOW_NOTIFICATION, title='Auto Clicker set!',
                             message="{} has set the auto clicker's interval to {} minutes".format(name, interval))
        else:
            self.server.push(CODE_SHOW_NOTIFICATION, title='Auto Clicker Stopped',
                             message="{} has disabled the auto clicker.".format(name))

    def handle_get_server_info(self, **_):
        from time import time
        return dict(
            server_time=time(),
            auto_clicker_interval=self.server.auto_clicker_interval,
            auto_clicker_seconds_left_for_interval=self.server.auto_clicker_thread.seconds_left_for_interval
            if self.server.auto_clicker_thread else None
        )

    def handle_get_temperature(self, **_):
        return dict(temperature=self.server.temperature)


class Server(ThreadingTCPServer):
    def __init__(self, name, server_address, handler=None):
        ThreadingTCPServer.__init__(self, server_address, handler)
        self.name = name


class MainServer(Server):
    def __init__(self, server_name, server_address):
        from serial_api import Clicker

        Server.__init__(self, server_name, server_address, handler=MainServerHandler)
        self.clients = {}
        self.timeout = 5
        self.auto_clicker_interval = None
        self.auto_clicker_thread = None  # type: RepeatingThread
        self.temperature = None  # type: float
        self.temperature_refresher_thread = RepeatingThread(20, self.update_temperature)
        self.temperature_refresher_thread.start()
        self._clicker = Clicker()
        self._is_last_clicked_on = False
        self.update_temperature()

    def push(self, code, **kwargs):
        from client import Client
        from datetime import datetime
        for client_ip, (client_port, registration_time) in self.clients.items():
            if (datetime.now() - datetime.fromtimestamp(registration_time)).total_seconds() > SESSION_TIMEOUT:
                self.clients.pop(client_ip)
                continue
            try:
                client = Client(client_ip, client_port, password=ServerSettings().server_password,
                                is_password_hashed=True, client_name=self.name)
                client.send(code, **kwargs)
            except:
                pass

    def set_auto_clicker(self, interval):
        assert isinstance(interval, (int, type(None)))
        self.auto_clicker_interval = interval
        if self.auto_clicker_thread:
            self.auto_clicker_thread.stop_event.set()
        if interval is not None:
            interval *= 60
            self.auto_clicker_thread = RepeatingThread(interval, self.click)
            self.auto_clicker_thread.start()
        self.push(CODE_AUTO_CLICKER_CHANGED, new_interval=interval)

    def click(self):
        import datetime
        print 'Click', datetime.datetime.now()
        if self.auto_clicker_thread:
            self.auto_clicker_thread.seconds_left_for_interval = self.auto_clicker_thread.interval
        try:
            if self._clicker.is_click2_enabled():
                if self._is_last_clicked_on:
                    self._clicker.click2()
                    self._is_last_clicked_on = False
                else:
                    self._clicker.click()
                    self._is_last_clicked_on = True
            else:
                self._clicker.click()
        except:
            raise NoClickerError("Error communicating with the clicker. It's possible it's not connected.")
        else:
            self.push(CODE_CLICK_HAPPENED)

    def update_temperature(self):
        try:
            self.temperature = self._clicker.temperature
        except:
            self.temperature = None

    def server_close(self):
        if self.auto_clicker_thread:
            self.auto_clicker_thread.stop_event.set()
            self.auto_clicker_thread.join()
        if self.temperature_refresher_thread:
            self.temperature_refresher_thread.stop_event.set()
            self.temperature_refresher_thread.join()
        Server.server_close(self)


def answer_search_requests(threaded=True):
    try:
        server = ThreadingUDPServer(('0.0.0.0', SERVER_BROADCAST_PORT), UDPBroadcastsHandler)
    except socket.error as error:
        print error
        return None
    return _init_server(server, threaded)


def run_server(threaded=True):
    try:
        settings = ServerSettings()
        server = MainServer(settings.server_name, ('0.0.0.0', settings.server_port))
    except socket.error as error:
        print error
        return None
    return _init_server(server, threaded)


def _init_server(server, threaded=True):
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server
    else:
        server.serve_forever()


class RepeatingThread(Thread):
    def __init__(self, interval_in_seconds, method):
        super(RepeatingThread, self).__init__()
        interval_in_seconds = int(interval_in_seconds)
        if interval_in_seconds < 1:
            interval_in_seconds = 1
        self.stop_event = Event()
        self.interval = interval_in_seconds
        self.seconds_left_for_interval = self.interval - 1
        self.method = method

    def run(self):
        while not self.stop_event.wait(1):
            if self.seconds_left_for_interval > 0:
                self.seconds_left_for_interval -= 1
            else:
                self.seconds_left_for_interval = self.interval - 1
                self.method()


if __name__ == '__main__':
    answer_search_requests(True)
    run_server(False)


class NoClickerError(Exception): pass