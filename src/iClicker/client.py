import hashlib
import hmac
import json
import time
from socket import *

from consts import *
from server import BaseServerHandler, _init_server, Server
from settings import ClientSettings


def find_servers():
    ip_addresses = sorted([address_info[4][0] for address_info in getaddrinfo(gethostname(), None, AF_INET)])

    for interface in ip_addresses:
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.bind((interface, 0))
        s.sendto(json.dumps(dict(code=CODE_FIND_SERVER)), ('255.255.255.255', SERVER_BROADCAST_PORT))
        s.settimeout(0.5)
        start_time = time.time()

        def receive():
            try:
                d = s.recvfrom(1024)
            except timeout:
                return None
            return d
        found_servers = set()
        data = receive()
        while data or ((time.time() - start_time) < FIND_SERVER_TIMEOUT):
            if data:
                data, (ip_address, _) = json.loads(data[0]), data[1]
                server_info = (data['server_name'], ip_address, data['port'])
                if server_info not in found_servers:
                    found_servers.add(server_info)
                    yield interface, server_info
            yield interface, None
            data = receive()


class BadPasswordException(Exception):
    def __init__(self, server_name, server_ip, server_port):
        self.server_name, self.server_ip, self.server_port = (server_name, server_ip, server_port)

    def __str__(self):
        try:
            server_name = '"{}" '.format(str(self.server_name))
        except (UnicodeDecodeError, UnicodeEncodeError):
            server_name = ''
        return "Bad Password for {}{}:{}".format(server_name, self.server_ip, self.server_port)


class Client(object):
    def __init__(self, server_address=None, port=None, password=None, client_name=None, is_password_hashed=False,
                 notifications_server_port=None):
        client_settings = ClientSettings()
        self.server_address = server_address or client_settings.connected_server[1]
        self.server_name = self.server_address
        self.port = port or client_settings.connected_server[2]
        self.socket = None
        self.client_name = client_name or client_settings.client_name
        if password:
            self.password = password if is_password_hashed else hashlib.sha1(password).hexdigest()
        else:
            self.password = client_settings.server_password
        self.notifications_server_port = notifications_server_port

    def _connect(self):
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect((self.server_address, self.port))

    def _send(self, code, **kwargs):
        self._connect()
        kwargs['code'] = code
        kwargs['name'] = self.client_name
        self.socket.send(json.dumps(kwargs))
        self._challenge()

    def connect(self):
        self.send(CODE_START_COMM, notifications_server_port=self.notifications_server_port)
        return self.send_receive(CODE_GET_SERVER_INFO)[1]

    def send(self, code, **kwargs):
        self._send(code, **kwargs)
        self.close()

    def send_receive(self, code, **kwargs):
        self._send(code, **kwargs)
        val = self.receive()
        self.close()
        return val

    def receive(self):
        data = self.socket.recv(1024)
        if data:
            try:
                data = json.loads(data)
                if 'name' in data:
                    self.server_name = data['name']
                return data['code'], data
            except:
                print data
                raise
        else:
            return None, None

    def _challenge(self):
        code, data = self.receive()
        if code is CODE_CHALLENGE_NOT_REQUIRED:
            response = None
        else:
            assert code is CODE_CHALLENGE_START, code
            challenge = data['challenge']
            password = hashlib.sha1(self.password or '').hexdigest()
            response = hmac.new(str(challenge), str(password), hashlib.sha1).hexdigest()
        self.socket.send(json.dumps(dict(code=CODE_CHALLENGE_RESPONSE, response=response)))
        if self.receive()[0] != CODE_CHALLENGE_SUCCESS:
            raise BadPasswordException(data['name'], self.server_address, self.port)
        return response

    def server_info(self):
        return self.send_receive(CODE_GET_SERVER_INFO)[1]

    def click(self):
        self.send_receive(CODE_CLICK)

    def get_temperature(self):
        return self.send_receive(CODE_GET_TEMPERATURE)[1]['temperature']

    def set_auto_clicker(self, interval):
        self.send_receive(CODE_SET_AUTO_CLICKER, interval=interval)

    def close(self):
        self.socket.close()


def run_client_notifications_receiver(threaded=True, handlers=None):
    class ClientUpdatesHandler(BaseServerHandler):
        def handlers(self):
            return handlers or {}

    try:
        server = Server(ClientSettings().client_name,
                        ('0.0.0.0', CLIENT_LISTENER_PORT), handler=ClientUpdatesHandler)
    except error as err:
        print err
        return None
    return _init_server(server, threaded)
