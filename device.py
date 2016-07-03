"""
Device class for Jumping Sumo
Returns binary data to send to Sumo
Extend this class to provide additional capacities
"""
import struct

SUMO_NACK_TYPE = 2
COMMON_PROJECT = 0
SUMO_PROJECT = 3
SUMO_CMD_BUFFER = 10
# SET_SPEED_TEMPLATE = [
    # '<BBBIBBHBbb',
    # 2, 10, 0, 14, 3, 0, 0, 1, 0, 0
# ]


class PilotingCommand(object):
    type = SUMO_NACK_TYPE
    buffer = SUMO_CMD_BUFFER
    sequence = 1


class SpeedAndCapCommand(PilotingCommand):
    format = '<BBBIBBHBbb'
    length = 14
    project = 3
    class_ = 0
    cmd = 0

    @classmethod
    def data(cls, sequence, speed, cap, boolean=1):
        assert speed <= 100 and speed >= -100
        assert cap <= 100 and cap >= -100
        return struct.pack(
            cls.format, cls.type, cls.buffer, sequence, cls.length,
            cls.project, cls.class_, cls.cmd,
            boolean, speed, cap)

SUMO_START_VID = struct.pack(
    '<BBBIBBHB', 0x02, 0x0a, 0x01, 0x0000000c, 0x03, 0x12, 0x00, 1)
SUMO_GET_SETTINGS = struct.pack(
    '<BBBIBBH', 0x02, 0x0a, 0x00, 0x0000000b, 0x00, 0x02, 0x0000)
SUMO_GET_STATES = struct.pack(
    '<BBBIBBH', 0x02, 0x0a, 0x00, 0x0000000b, 0x00, 0x04, 0x0000)
SUMO_START_ANIM = struct.pack(
    '<BBBIBBHI', 0x02, 0x0a, 0x01, 0x0000000f, 0x03, 0x02, 0x04, 0x00000006)
SUMO_STOP_ANIM = struct.pack(
    '<BBBIBBHI', 0x02, 0x0a, 0x02, 0x0000000f, 0x03, 0x02, 0x04, 0x00000000)
SUMO_START_MOTOR = struct.pack(
    '<BBBIBBHBbb', 0x02, 0x0a, 0x01, 0x0000000e, 0x03, 0x0, 0x0, 1, 50, 0)
SUMO_STOP_MOTOR = struct.pack(
    '<BBBIBBHBbb', 0x02, 0x0a, 0x02, 0x0000000e, 0x03, 0x0, 0x0, 0, 0, 0)
