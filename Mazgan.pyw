from optparse import OptionParser


def main():
    parser = OptionParser()
    parser.add_option('-s', '--server', dest='server_mode', action='store_true', help='Run as a server (in CLI mode).')
    parser.add_option('-c', '--client', dest='client_mode', action='store_true', help='Run as a client (in CLI mode).')

    options, args = parser.parse_args()
    if options.server_mode:
        from server import answer_search_requests
        answer_search_requests(threaded=False)
    elif options.client_mode:
        from client import find_servers
        print find_servers()
    else:
        from gui.gui import main
        main()

if __name__ == '__main__':
    main()
