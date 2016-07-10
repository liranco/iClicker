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
    s.settimeout(2)
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
            found_servers.add((data['server_name'], data['port'], ip_address))
        data = receive()
    return found_servers
