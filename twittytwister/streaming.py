# -*- test-case-name: twittytwister.test.test_streaming -*-
#
# Copyright (c) 2010-2012 Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Twitter Streaming API.

@see: U{http://dev.twitter.com/pages/streaming_api}.
"""

import simplejson as json

from twisted.internet import defer
from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin
from twisted.python import log
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

from twittytwister import platform

class LengthDelimitedStream(LineReceiver):
    """
    Length-delimited datagram decoder protocol.

    Datagrams are prefixed by a line with a decimal length in ASCII. Lines are
    delimited by C{\r\n} and maybe empty, for keep-alive purposes.
    """

    def __init__(self):
        self._rawBuffer = None
        self._rawBufferLength = None
        self._expectedLength = None


    def lineReceived(self, line):
        """
        Called when a line is received.

        We expect a length in bytes or an empty line for keep-alive. If
        we got a length, switch to raw mode to receive that amount of bytes.
        """
        if line and line.isdigit():
            self._expectedLength = int(line)
            self._rawBuffer = []
            self._rawBufferLength = 0
            self.setRawMode()
        else:
            self.keepAliveReceived()


    def rawDataReceived(self, data):
        """
        Called when raw data is received.

        Fill the raw buffer C{_rawBuffer} until we have received at least
        C{_expectedLength} bytes. Call C{datagramReceived} with the received
        byte string of the expected size. Then switch back to line mode with
        the remainder of the buffer.
        """
        self._rawBuffer.append(data)
        self._rawBufferLength += len(data)

        if self._rawBufferLength >= self._expectedLength:
            receivedData = ''.join(self._rawBuffer)
            expectedData = receivedData[:self._expectedLength]
            extraData = receivedData[self._expectedLength:]

            self._rawBuffer = None
            self._rawBufferLength = None
            self._expectedLength = None

            self.datagramReceived(expectedData)
            self.setLineMode(extraData)


    def datagramReceived(self, data):
        """
        Called when a datagram is received.
        """
        raise NotImplementedError()


    def keepAliveReceived(self):
        """
        Called when a empty line as keep-alive is received.

        This can be overridden for logging purposes.
        """



class TwitterStream(LengthDelimitedStream, TimeoutMixin):
    """
    Twitter Stream.

    This protocol decodes an JSON encoded stream of Twitter statuses and
    associated datastructures, where each datagram is length-delimited.

    L{TimeoutMixin} is used to disconnect the stream in case Twitter stops
    sending data, including the keep-alives that usually result in traffic
    at least every 30 seconds. If not passed using C{timeoutPeriod}, the
    timeout period is set to 60 seconds.
    """

    def __init__(self, callback, timeoutPeriod=60):
        LengthDelimitedStream.__init__(self)
        self.setTimeout(timeoutPeriod)
        self.callback = callback
        self.deferred = defer.Deferred()


    def dataReceived(self, data):
        """
        Called when data is received.

        This overrides the default implementation from LineReceiver to
        reset the connection timeout.
        """
        self.resetTimeout()
        LengthDelimitedStream.dataReceived(self, data)


    def datagramReceived(self, data):
        """
        Decode the JSON-encoded datagram and call the callback.
        """
        try:
            obj = json.loads(data)
        except ValueError, e:
            log.err(e, 'Invalid JSON in stream: %r' % data)
            return

        if u'text' in obj:
            obj = platform.Status.fromDict(obj)
        else:
            log.msg('Unsupported object %r' % obj)
            return

        self.callback(obj)


    def connectionLost(self, reason):
        """
        Called when the body is complete or the connection was lost.

        @note: As the body length is usually not known at the beginning of the
        response we expect a L{PotentialDataLoss} when Twitter closes the
        stream, instead of L{ResponseDone}. Other exceptions are treated
        as error conditions.
        """
        self.setTimeout(None)
        if reason.check(ResponseDone, PotentialDataLoss):
            self.deferred.callback(None)
        else:
            self.deferred.errback(reason)


    def timeoutConnection(self):
        """
        Called when the connection times out.

        This protocol is used to process the HTTP response body. Its transport
        is really a proxy, that does not provide C{loseConnection}. Instead it
        has C{stopProducing}, which will result in the real transport being
        closed when called.
        """
        self.transport.stopProducing()
