from ..api import api

import getpass

def logout(accessor):
    if accessor:
        print "Disconnected from " + accessor.server_url
        accessor=None
    else:
        print "Not connected"
    return None


def login(server_url,username=""):
    if not username:
        print "NetID:"
        username = raw_input()
    
    print "Password:"
    password = getpass.getpass()

    accessor = api.server_accessor(server_url,username=username,password=password)

    if accessor.check_connection():
        print "Connected to " + accessor.server_url
        return accessor
    else:
        print "No connection"
        accessor=None
    return accessor
