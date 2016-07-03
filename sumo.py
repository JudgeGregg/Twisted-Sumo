"""
Main Sumo control module

Setup TCP and UDP protocols
Setup Web Iface

"""
import json
import time
import struct
from collections import defaultdict, OrderedDict
from sys import stdout

from twisted.internet import reactor, task
from twisted.internet.protocol import Protocol, DatagramProtocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.python.log import startLogging
from twisted.web.resource import Resource
from twisted.web.server import Site

from device import SpeedAndCapCommand, SUMO_START_VID
from iface import Base, Video, Speed

SUMO_IP = '192.168.2.1'
SUMO_TCP_PORT = 44444
SUMO_D2C = 43210
SUMO_C2D = 54321

WEB_IFACE_PORT = 8880

# Sumo Handshake
JSON_PAYLOAD = json.dumps(
    {"d2c_port": SUMO_D2C, "controller_type": "Desktop",
     "controller_name": "net.judge-gregg.arsdkapp"})


class SumoStateHolder(object):
    """Share state between web iface and protocols"""

    def __init__(self):
        self.time_frame = 0
        self.cap = 0
        self.speed = 0
        self.frame = ''
        self.sequence = 1


class SumoGreeter(Protocol):
    """Send JSON payload to greet Sumo"""
    def sendMessage(self, msg):
        print 'sending'
        self.transport.write(msg+'\n')

    def lineReceived(self, line):
        print line

    def dataReceived(self, data):
        print 'receiving'
        print data


def gotProtocol(p, state_holder):
    """One-shot method to open UDP socket"""
    # TCP Connection initialised
    p.sendMessage(JSON_PAYLOAD)
    reactor.callLater(
        1, reactor.listenUDP, SUMO_D2C, SumoListen(state_holder),
        maxPacketSize=65020)


class SumoListen(DatagramProtocol):

    def __init__(self, state_holder):
        self.state = state_holder

    def update_speed(self):
        print self.state.speed, self.state.cap
        data = SpeedAndCapCommand.data(
            self.state.sequence, self.state.speed, self.state.cap)
        self.state.sequence += 1
        # Reset sequence number
        if self.state.sequence > 255:
            self.state.sequence = 1
        self.transport.write(data, (SUMO_IP, SUMO_C2D))

    def startProtocol(self):
        # UDP Protocol started
        # Start emitting video
        self.frames = defaultdict(dict)
        reactor.callLater(1, self.transport.write, SUMO_START_VID, (
            SUMO_IP, SUMO_C2D))
        self.state.sequence += 1
        task.LoopingCall(self.update_speed).start(0.05)

    def datagramReceived(self, data, (host, port)):
        self.handle_data(data, (host, port))

    def handle_data(self, data, (host, port)):
        """Handle data frame."""
        # TODO: Split in multiple funcs
        header = data[:7]
        type_, buffer_id, sequence, length = struct.unpack('<BBBI', header)
        if type_ == 4:
            proj, class_, cmd = struct.unpack('<BBH', data[7:11])
            if (proj, class_, cmd) == (0, 5, 1):
                bat_level = data[11]
                print 'BAT_LVL: ' + str(ord(bat_level))
            proj, class_, cmd = struct.unpack('<BBH', data[7:11])
            if (proj, class_, cmd) == (3, 11, 4):
                link_qual = data[11]
                print 'LINK QUALITY CHANGED' + str(ord(link_qual))
                self.transport.write(SUMO_START_VID, (host, SUMO_C2D))
            print 'ACK'
            # Ack required.
            ack_buffer_id = buffer_id + 128
            ack_frame = struct.pack(
                '<BBBIB', 0x01, ack_buffer_id, 0x01, 0x00000008, sequence)
            self.transport.write(ack_frame, (host, SUMO_C2D))
        elif type_ == 3 and buffer_id == 125:
            # Video Frame received.
            header, frame = data[:12], data[12:]
            frame_num, flag, nbr, per_fr = struct.unpack('<HBBB', header[7:])
            if per_fr == 1:
                self.state.frame = frame
                self.state.time_frame = time.time()
                print 'FRAME' + str(len(frame))
            else:
                self.frames[frame_num][frame] = nbr
                if len(self.frames[frame_num]) == per_fr:
                    frame_to_be = ''
                    fra = OrderedDict(sorted(
                        self.frames[frame_num].items(), key=lambda t: t[1]))
                    for frag in fra.keys():
                        frame_to_be += frag
                    self.state.frame = frame_to_be
                    self.state.time_frame = time.time()
                    print 'FRAME' + str(len(frame_to_be))
                    del self.frames[frame_num]
        elif type_ == 2 and buffer_id == 0:
            secs, nano_secs = struct.unpack('<II', data[7:length])
            ack_frame = struct.pack(
                '<BBBIII', 0x02, 1, sequence, length, secs, nano_secs)
            self.transport.write(ack_frame, (host, SUMO_C2D))
        elif type_ == 2 and buffer_id == 127:
            proj, class_, cmd = struct.unpack('<BBH', data[7:11])
            if (proj, class_, cmd) == (0, 5, 7):
                signal = data[11:12]
                print 'WIFI CHANGED: ' + str(ord(signal))
        if len(data) > length:
            # Another frame is available
            self.handle_data(data[length:], (host, port))

# Initialise connections
endpoint = TCP4ClientEndpoint(reactor, SUMO_IP, SUMO_TCP_PORT)
state_holder = SumoStateHolder()
d = connectProtocol(endpoint, SumoGreeter())
d.addCallback(gotProtocol, state_holder)

# Initialise Web Iface
root = Resource()
root.putChild('video', Video(state_holder))
root.putChild('home', Base())
root.putChild('speed', Speed(state_holder))

factory = Site(root)
reactor.listenTCP(WEB_IFACE_PORT, factory)

startLogging(stdout)
reactor.run()
