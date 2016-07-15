import json
from consts import *
from utils import Settings
from threading import Thread
import SocketServer


class BroadcastsHandler(SocketServer.DatagramRequestHandler):
    def handle(self):
        data = json.loads(self.rfile.read())
        code = data['code']
        if code == CODE_FIND_SERVER:
            self.wfile.write(json.dumps(dict(server_name=Settings().server_name, port=Settings().server_port)))


def answer_search_requests(threaded=True):
    try:
        server = SocketServer.ThreadingUDPServer(('0.0.0.0', SERVER_BROADCAST_PORT), BroadcastsHandler)
    except SocketServer.socket.error:
        return
    if threaded:
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        return server_thread
    else:
        server.serve_forever()


def run_server(threaded=True):
    pass