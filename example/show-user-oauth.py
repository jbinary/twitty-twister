#!/usr/bin/env python
"""

Copyright (c) 2009  Kevin Dunglas <dunglas@gmail.com>
"""

import sys

from twisted.internet import reactor
from twisted.python import log

from twittytwister import twitter
from oauth import oauth

def gotUser(u):
    print "Got a user: %s" % u

consumer = oauth.OAuthConsumer(sys.argv[1], sys.argv[2])
token = oauth.OAuthToken(sys.argv[3], sys.argv[4])

api = twitter.Twitter(consumer=consumer, token=token)
d = api.show_user(screen_name=sys.argv[5])
d.addCallback(gotUser)
d.addErrback(log.err)
d.addBoth(lambda x: reactor.stop())

reactor.run()
