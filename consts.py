from itertools import count as _count

# General settings
SERVER_MODE = 'Server'
CLIENT_MODE = 'Client'

# Ports
SERVER_BROADCAST_PORT = 1919
DEFAULT_SERVER_PORT = 9191
CLIENT_LISTENER_PORT = 1991


# ### Communications Codes ### #
_next = _count(1).next
# basic codes
CODE_FIND_SERVER = _next()
CODE_START_COMM = _next()
CODE_SERVER_RESPONSE = _next()
# challenge-response codes
CODE_CHALLENGE_START = _next()
CODE_CHALLENGE_NOT_REQUIRED = _next()
CODE_CHALLENGE_RESPONSE = _next()
CODE_CHALLENGE_FAILED = _next()
CODE_CHALLENGE_SUCCESS = _next()
# instruction codes
CODE_SAY_HELLO = _next()
CODE_GET_SERVER_INFO = _next()
CODE_CLICK = _next()
CODE_SET_AUTO_CLICKER = _next()
# Events codes
CODE_SHOW_NOTIFICATION = _next()
CODE_CLICK_HAPPENED = _next()
CODE_AUTO_CLICKER_CHANGED = _next()

# Server Settings
FIND_SERVER_TIMEOUT = 5  # 5 Seconds
SESSION_TIMEOUT = 20     # 20 Seconds


if __name__ == '__main__':
    # Print all codes
    print "\r\n".join(
        map(lambda item: ": ".join((item[0], str(item[1]))),
            sorted(
                filter(lambda item: item[0].startswith('CODE_'),
                       globals().iteritems()), key=lambda item: item[1])))
