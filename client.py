import hashlib
import hmac
import json
from settings import Settings
from consts import *
from time import time
from socket import *
import time


def find_servers():
    ip_addresses = sorted([address_info[4][0] for address_info in getaddrinfo(gethostname(), None, AF_INET)])

    for interface in ip_addresses:
        s = socket(AF_INET, SOCK_DGRAM)
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        s.bind((interface, 0))
        s.sendto(json.dumps(dict(code=CODE_FIND_SERVER)), ('255.255.255.255', SERVER_BROADCAST_PORT))
        s.settimeout(0.5)
        start_time = time()

        def receive():
            try:
                d = s.recvfrom(1024)
            except timeout:
                return None
            return d
        found_servers = set()
        data = receive()
        while data or ((time() - start_time) < FIND_SERVER_TIMEOUT):
            if data:
                data, (ip_address, _) = json.loads(data[0]), data[1]
                server_info = (data['server_name'], ip_address, data['port'])
                if server_info not in found_servers:
                    found_servers.add(server_info)
                    yield interface, server_info
            yield interface, None
            data = receive()


class Client(object):
    def __init__(self, server_address='192.168.1.19', port=9191):
        self.server_address = server_address
        self.port = port
        self.socket = socket(AF_INET, SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.server_address, self.port))
        self.send(CODE_START_COMM)

    def send(self, code, **kwargs):
        kwargs['code'] = code
        self.socket.send(json.dumps(kwargs))
        self._challenge()

    def receive(self):
        data = self.socket.recv(1024)
        if data:
            data = json.loads(data)
            return data['code'], data
        else:
            return None, None

    def _challenge(self):
        code, data = self.receive()
        assert code == CODE_CHALLENGE_START
        challenge = data['challenge']
        password = hashlib.sha1(Settings().server_settings.server_password[0]).hexdigest()
        response = hmac.new(str(challenge), str(password), hashlib.sha1).hexdigest()
        self.socket.send(json.dumps(dict(code=CODE_CHALLENGE_RESPONSE, response=response)))
        assert self.receive()[0] == CODE_CHALLENGE_SUCCESS
        return response

    def dance(self):
        self.send(CODE_SAY_HELLO)
        self.send(CODE_ACCEPT_NOTIFICATIONS)

    def close(self):
        self.socket.close()


if __name__ == '__main__':
    client = Client()
    print "Connecting"
    client.connect()
    print "Dancing"
    client.dance()
    client.close()
