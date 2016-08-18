from consts import *
from settings import ServerSettings
from threading import Thread, Event
from SocketServer import *
import socket
import json
import hmac
import hashlib
import os
import time


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
        kwargs['name'] = self.server.server_name
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
            CODE_SAY_HELLO: self.handle_say_hello,
            CODE_ACCEPT_NOTIFICATIONS: self.handle_accept_notifications,
            CODE_CLICK: self.handle_click,
            CODE_SET_AUTO_CLICKER: self.handle_set_auto_clicker,
            CODE_GET_SERVER_INFO: self.get_server_info
        }

    def handle_say_hello(self, name, **_):
        self._post(CODE_SERVER_RESPONSE, message='Hello from {}'.format(ServerSettings().server_name))
        if self.server.updates_method:
            self.server.updates_method('Say Hello!', 'HELLOOOOO from {}'.format(name))

    def handle_accept_notifications(self, **_):
        self.server.clients[self.client_address[0]] = (self.client_address[1], time.time())
        self.server.updates_method('Connected Servers', '\r\n'.join(self.server.clients))

    def handle_click(self, name, **_):
        print _
        self.server.click()
        self.server.updates_method('Click!', '{} has sent a click command'.format(name))

    def handle_set_auto_clicker(self, name, interval, **_):
        assert isinstance(interval, (int, type(None)))
        if isinstance(interval, int) and interval <= 0:
            interval = None
        self.server.set_auto_clicker(interval)
        if interval:
            self.server.updates_method('Auto Clicker set!', "{} has set the auto clicker's interval to {} minutes"
                                       .format(name, interval))
        else:
            self.server.updates_method('Auto Clicker disabled!', "{} has disabled the auto clicker".format(name))

    def get_server_info(self, **_):
        from time import time
        return dict(
            server_time=time(),
            auto_clicker_interval=self.server.auto_clicker_interval,
            auto_clicker_seconds_left_for_interval=self.server.auto_clicker_thread.seconds_left_for_interval
            if self.server.auto_clicker_thread else None
        )


class MainServer(ThreadingTCPServer):
    def __init__(self, server_name, server_address, updates_method=None, handler=MainServerHandler):
        ThreadingTCPServer.__init__(self, server_address, handler)
        self.clients = {}
        self.server_name = server_name
        self.timeout = 5
        self.updates_method = updates_method or self._auto_updates_method
        self.auto_clicker_interval = None
        self.auto_clicker_thread = None  # type: AutoClicker

    @staticmethod
    def _auto_updates_method(title, message):
        print '{}: {}'.format(title, message)

    def set_auto_clicker(self, interval):
        assert isinstance(interval, (int, type(None)))
        self.auto_clicker_interval = interval
        if self.auto_clicker_thread:
            self.auto_clicker_thread.stop_event.set()
        if interval is not None:
            self.auto_clicker_thread = AutoClicker(interval)
            self.auto_clicker_thread.start()

    def click(self):
        print 'Manual Click!'
        if self.auto_clicker_thread:
            self.auto_clicker_thread.seconds_left_for_interval = self.auto_clicker_thread.interval

    def server_close(self):
        if self.auto_clicker_thread:
            self.auto_clicker_thread.stop_event.set()
            self.auto_clicker_thread.join()


def answer_search_requests(threaded=True):
    try:
        server = ThreadingUDPServer(('0.0.0.0', SERVER_BROADCAST_PORT), UDPBroadcastsHandler)
    except socket.error as error:
        print error
        return None, None
    return _init_server(server, threaded)


def run_server(threaded=True, updates_method=None, handler=MainServerHandler):
    try:
        settings = ServerSettings()
        server = MainServer(settings.server_name, ('0.0.0.0', settings.server_port),
                            updates_method, handler)
    except socket.error as error:
        print error
        return None, None
    return _init_server(server, threaded)


def _init_server(server, threaded=True):
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread, server
    else:
        server.serve_forever()


class AutoClicker(Thread):
    def __init__(self, interval_in_minutes):
        super(AutoClicker, self).__init__()
        interval_in_minutes = int(interval_in_minutes)
        if interval_in_minutes < 1:
            interval_in_minutes = 1
        self.stop_event = Event()
        self.interval = interval_in_minutes
        self.seconds_left_for_interval = self.interval - 1

    def run(self):
        while not self.stop_event.wait(1):
            print self.seconds_left_for_interval
            if self.seconds_left_for_interval > 0:
                self.seconds_left_for_interval -= 1
            else:
                print 'Auto Click!'
                self.seconds_left_for_interval = self.interval - 1


if __name__ == '__main__':
    answer_search_requests(True)
    run_server(False)
