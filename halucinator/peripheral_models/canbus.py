# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from . import peripheral_server
#from queue import Queue
from threading import Event, Thread
from collections import deque, defaultdict
import sys
import logging
from itertools import repeat
import time

log = logging.getLogger("CANBUSModel")
log.setLevel(logging.DEBUG)

# CAN Frames are detailed here: https://en.wikipedia.org/wiki/CAN_bus


def can_crc15(framebytes):
    pass

""" CAN 2.0 A (11-bit ID) Frame """
class CANFrame(object):

    def __init__(self, framebytes):
        pass

""" CAN 2.0 A (11-bit ID) Frame """
class CANFrameExtended(object):

    def __init__(self, framebytes):
        pass


    def __repr__(self):
        rep = ''
        
        def binary(word):
            '{0:b}'.format(word)


    @classmethod
    def try_decode_frame(framebytes):

        if len(framebytes) < 8:
            raise Exception("Frame size is not long enough")
        id_extension_bit = framebytes[0] & 0x04

        if id_extension_bit != 1:
            raise Exception("ID bit must be recessive (1) for extended frames")

        id_extension=1

        identifier_part_a = framebytes[0] & 0x7FF0

        identifier_part_b1 = framebytes[0] & 0x0003
        identifier_part_b2 = framebytes[1] 
        identifier_part_b = (identifier_part_b1 << 16) | identifier_part_b2
        identifier = identifier_part_a << 18 | identifier_part_b

        datalen = framebytes[2] & 0x1E00
        if datalen < 0 or datalen > 8:
            raise Exception("Datalen parsing error")

        databits = 8*datalen
        

        self.frame = framebytes:

def ParseCANFrame(framebytes):

    frame = CANFrameExtended.try_decode_frame(framebytes)
    if frame is not None:
        return frame

    frame = CANFrame.try_decode_frame(framebytes)
    if frame is not None:
        return frame

    raise Exception("Unable to parse CAN Frame")


# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class CANPublisher(object):
    rx_buffers = defaultdict(deque)

    @classmethod
    @peripheral_server.tx_msg
    def write(cls, CAN_id, chars):
        '''
           Publishes the data to sub/pub server
        '''
        log.debug("In: CANPublisher.write: %s" % chars)
        msg = {'id': CAN_id, 'chars': chars}
        return msg

    @classmethod
    def read(cls, CAN_id, count=1, block=False):
        '''
            Gets data previously received from the sub/pub server
            Args:
                CAN_id:   A unique id for the CAN
                count:  Max number of chars to read
                block(bool): Block if data is not available
        '''
        log.debug("In: CANPublisher.read id:%s count:%i, block:%s" %
                  (hex(CAN_id), count, str(block)))
        while block and (len(cls.rx_buffers[CAN_id]) < count):
            pass
        log.debug("Done Blocking: CANPublisher.read")
        buffer = cls.rx_buffers[CAN_id]
        chars_available = len(buffer)
        if chars_available >= count:
            chars = [buffer.popleft() for _ in range(count)]
            chars = ''.join(chars).encode('utf-8')
        else:
            chars = [buffer.popleft() for _ in range(chars_available)]
            chars = ''.join(chars).encode('utf-8')

        return chars

    @classmethod
    @peripheral_server.reg_rx_handler
    def rx_data(cls, msg):
        '''
            Handles reception of these messages from the PeripheralServer
        '''
        log.debug("rx_data got message: %s" % str(msg))
        CAN_id = msg['id']
        data = msg['chars']
        cls.rx_buffers[CAN_id].extend(data)
