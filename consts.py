from itertools import count as _count

# General settings
SERVER_MODE = 'Server'
CLIENT_MODE = 'Client'

# Ports
SERVER_BROADCAST_PORT = 1919
DEFAULT_SERVER_PORT = 9191


# ### Communications Codes ### #
_code_counter = _count(1)
# basic codes
CODE_FIND_SERVER = _code_counter.next()
CODE_START_COMM = _code_counter.next()
CODE_SERVER_RESPONSE = _code_counter.next()
# challenge-response codes
CODE_CHALLENGE_START = _code_counter.next()
CODE_CHALLENGE_NOT_REQUIRED = _code_counter.next()
CODE_CHALLENGE_RESPONSE = _code_counter.next()
CODE_CHALLENGE_FAILED = _code_counter.next()
CODE_CHALLENGE_SUCCESS = _code_counter.next()
# instruction codes
CODE_SAY_HELLO = _code_counter.next()
CODE_ACCEPT_NOTIFICATIONS = _code_counter.next()
CODE_CLICK = _code_counter.next()
CODE_SET_AUTO_CLICKER = _code_counter.next()

# Server Settings
FIND_SERVER_TIMEOUT = 5  # 5 Seconds
SESSION_TIMEOUT = 5     # 20 Seconds
