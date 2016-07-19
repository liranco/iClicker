from consts import *
from settings import Settings
from threading import Thread
from SocketServer import *
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
        self.wfile.write(json.dumps(kwargs))

    def _get(self):
        data = self.request.recv(1024)
        if data:
            data = json.loads(data)
            return data['code'], data
        else:
            return None, None

    def handle(self):
        while True:
            code, data = self._get()
            if code is None:
                return
            if self.challenge_sequence():
                self._post(CODE_CHALLENGE_SUCCESS)
            else:
                self._post(CODE_CHALLENGE_FAILED)
                continue
            if code == CODE_SAY_HELLO:
                print 'HELLOOOOO'
                continue
            if code == CODE_ACCEPT_NOTIFICATIONS:
                self.server.clients[self.client_address[0]] = (self.client_address[1], time.time())
                print self.server.clients
                continue

    def challenge_sequence(self):
        # Start authentication
        challenge = os.urandom(16).encode('hex')
        password_hash = hashlib.sha1(Settings().server_settings.server_password).hexdigest()
        expected_response = hmac.new(challenge, password_hash, hashlib.sha1).hexdigest()

        self._post(CODE_CHALLENGE_START, challenge=challenge)
        code, result = self._get()
        assert code == CODE_CHALLENGE_RESPONSE
        response = result['response']
        if response != expected_response:
            return False
        else:
            return True


class MainServer(ThreadingTCPServer):
    def __init__(self, server_address):
        ThreadingTCPServer.__init__(self, server_address, MainServerHandler)
        self.clients = {}
        self.timeout = 5


def answer_search_requests(threaded=True):
    try:
        server = ThreadingUDPServer(('0.0.0.0', SERVER_BROADCAST_PORT), UDPBroadcastsHandler)
    except socket.error:
        return
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread, server
    else:
        server.serve_forever()


def run_server(threaded=True):
    try:
        server = MainServer(('0.0.0.0', Settings().server_settings.server_port))
    except socket.error:
        return
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread, server
    else:
        server.serve_forever()


if __name__ == '__main__':
    run_server(False)
