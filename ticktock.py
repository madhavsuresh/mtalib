#!/usr/bin/python2.7

from jobs import events

# config must define and configure the accessor
# config must add datehooks to the event module or nothing will happen
import config

if not config.api_server.check_connection():
    print "CANNOT CONNECT TO MECHANICAL TA AT\n\t %s" % config.api_server.server_url
    exit()

for c in config.courses:
    events.run(config.api_server,courseID=c,prompt=True)

