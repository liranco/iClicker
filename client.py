import json
from consts import *
from time import time
from socket import *


def find_servers():
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.bind(('192.168.1.19', 0))
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
                yield server_info
        yield None
        data = receive()
