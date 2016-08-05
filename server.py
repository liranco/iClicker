from consts import *
from settings import Settings
from threading import Thread
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
            settings = Settings().server_settings
            self.wfile.write(json.dumps(dict(server_name=settings.server_name, port=settings.server_port)))


class MainServerHandler(StreamRequestHandler):
    def __init__(self, request, client_address, server):
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

    def handle(self):
        code, data = self._get()
        if code is None:
            return
        if self.challenge_sequence():
            self._post(CODE_CHALLENGE_SUCCESS)
        else:
            self._post(CODE_CHALLENGE_FAILED)
            return
        if code == CODE_SAY_HELLO:
            print 'HELLOOOOO from ', data['name']
            return
        if code == CODE_ACCEPT_NOTIFICATIONS:
            self.server.clients[self.client_address[0]] = (self.client_address[1], time.time())
            print self.server.clients
            return

    def challenge_sequence(self):
        # Start authentication
        password = Settings().server_settings.server_password
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


class MainServer(ThreadingTCPServer):
    def __init__(self, server_name, server_address):
        ThreadingTCPServer.__init__(self, server_address, MainServerHandler)
        self.clients = {}
        self.server_name = server_name
        self.timeout = 5


def answer_search_requests(threaded=True):
    try:
        server = ThreadingUDPServer(('0.0.0.0', SERVER_BROADCAST_PORT), UDPBroadcastsHandler)
    except socket.error as error:
        print error
        return None, None
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread, server
    else:
        server.serve_forever()


def run_server(threaded=True):
    try:
        server = MainServer(Settings().server_settings.server_name, ('0.0.0.0', Settings().server_settings.server_port))
    except socket.error as error:
        print error
        return None, None
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread, server
    else:
        server.serve_forever()


if __name__ == '__main__':
    answer_search_requests(True)
    run_server(False)
