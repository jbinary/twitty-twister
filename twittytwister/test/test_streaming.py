# Copyright (c) 2010-2012 Ralph Meijer <ralphm@ik.nu>
# See LICENSE.txt for details

"""
Tests for L{twittytwister.streaming}.
"""

from twisted.internet import task
from twisted.python import failure
from twisted.test import proto_helpers
from twisted.trial import unittest
from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

from twittytwister import platform, streaming

class StreamTester(streaming.LengthDelimitedStream):
    """
    Test helper that stores all received datagrams in sequence.
    """
    def __init__(self):
        streaming.LengthDelimitedStream.__init__(self)
        self.datagrams = []
        self.keepAlives = 0


    def datagramReceived(self, data):
        self.datagrams.append(data)


    def keepAliveReceived(self):
        self.keepAlives += 1



class LengthDelimitedStreamTest(unittest.TestCase):
    """
    Tests for L{LengthDelimitedStream}.
    """

    def setUp(self):
        transport = proto_helpers.StringTransport()
        self.protocol = StreamTester()
        self.protocol.makeConnection(transport)


    def test_receiveDatagram(self):
        """
        A datagram is a length, CRLF and a sequence of bytes of given length.
        """
        self.protocol.dataReceived("""4\r\ntest""")
        self.assertEquals(['test'], self.protocol.datagrams)
        self.assertEquals(0, self.protocol.keepAlives)


    def test_receiveTwoDatagrams(self):
        """
        Two encoded datagrams should result in two calls to datagramReceived.
        """
        self.protocol.dataReceived("""4\r\ntest5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)
        self.assertEquals(0, self.protocol.keepAlives)


    def test_receiveKeepAlive(self):
        """
        Datagrams may have empty keep-alive lines in between.
        """
        self.protocol.dataReceived("""4\r\ntest\r\n5\r\ntest2""")
        self.assertEquals(['test', 'test2'], self.protocol.datagrams)
        self.assertEquals(1, self.protocol.keepAlives)


    def test_notImplemented(self):
        self.protocol = streaming.LengthDelimitedStream()
        self.assertRaises(NotImplementedError, self.protocol.dataReceived,
                                               """4\r\ntest""")



class TestableTwitterStream(streaming.TwitterStream):

    def __init__(self, _clock, *args, **kwargs):
        self._clock = _clock
        streaming.TwitterStream.__init__(self, *args, **kwargs)


    def callLater(self, *args, **kwargs):
        return self._clock.callLater(*args, **kwargs)



class TwitterStreamTest(unittest.TestCase):
    """
    Tests for L{streaming.TwitterStream}.
    """

    def setUp(self):
        self.objects = []
        self.transport = proto_helpers.StringTransport()
        self.clock = task.Clock()
        self.protocol = TestableTwitterStream(self.clock, self.objects.append)
        self.protocol.makeConnection(self.transport)


    def tearDown(self):
        self.protocol.setTimeout(None)


    def test_status(self):
        """
        Status objects become L{streaming.Status} objects passed to callback.
        """
        data = """{"text": "Test status"}\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(1, len(self.objects))
        self.assertIsInstance(self.objects[-1], platform.Status)


    def test_unknownObject(self):
        """
        Unknown objects are ignored.
        """
        data = """{"something": "Some Value"}\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(0, len(self.objects))


    def test_badJSON(self):
        """
        Datagrams with invalid JSON are logged and ignored.
        """
        data = """blah\n\r"""
        self.protocol.datagramReceived(data)
        self.assertEquals(0, len(self.objects))
        loggedErrors = self.flushLoggedErrors(ValueError)
        self.assertEquals(1, len(loggedErrors))


    def test_closedResponseDone(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(ResponseDone()))
        return self.protocol.deferred


    def test_closedPotentialDataLoss(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(PotentialDataLoss()))
        return self.protocol.deferred


    def test_closedOther(self):
        """
        When the connection is done, the deferred is fired.
        """
        self.protocol.connectionLost(failure.Failure(Exception()))
        self.assertFailure(self.protocol.deferred, Exception)


    def test_closedNoTimeout(self):
        """
        When the connection is done, there is no timeout.
        """
        self.protocol.connectionLost(failure.Failure(ResponseDone()))
        self.assertEquals(None, self.protocol.timeOut)
        return self.protocol.deferred


    def test_timeout(self):
        """
        When the timeout is reached, the transport should stop producing.

        A real transport would call connectionLost, but we don't need to test
        that here.
        """
        self.clock.advance(59)
        self.assertEquals('producing', self.transport.producerState)
        self.clock.advance(1)
        self.assertEquals('stopped', self.transport.producerState)


    def test_timeoutPostponedOnData(self):
        """
        When the timeout is reached, the transport stops producing.

        A real transport would call connectionLost, but we don't need to test
        that here.
        """
        self.clock.advance(20)
        data = """{"text": "Test status"}\n\r"""
        self.protocol.dataReceived(data)
        self.clock.advance(40)
        self.assertEquals('producing', self.transport.producerState,
                          "Unexpected timeout")
        self.clock.advance(20)
        self.assertEquals('stopped', self.transport.producerState)
