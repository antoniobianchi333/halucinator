
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

log = logging.getLogger("AmpDashModel")
log.setLevel(logging.DEBUG)

# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class AmpDashModel(object):
    rx_buffers = defaultdict(deque)

    @classmethod
    @peripheral_server.tx_msg
    def tx_data(cls, CAN_id, chars):
        """
        Emulator -> Peripheral Server
        This method receives data written to the peripheral in emulation land, 
        and sends it to the emulated peripheral directly.
        """
        log.debug("In: CanBus.write: %s" % chars)
        msg = {'id': CAN_id, 'chars': chars}
        return msg
    
    @classmethod
    @peripheral_server.reg_rx_handler
    def rx_data(cls, msg):
        """
        Peripheral Server -> Emulator
        This method receives data send from the peripheral device and buffers 
        it for intercepts of the read method.
        """
        log.debug("rx_data got message: %s" % str(msg))
        canid = msg['id']
        data = msg['data']
        cls.rx_buffers[canid].extend(data)

    @classmethod
    def read(cls, CAN_id, count=1, block=False):
        """
        This method is a firmware interception point for CANBus Read events.

        Args:
            CAN_id:   A unique id for the CAN
            count:  Max number of chars to read
            block(bool): Block if data is not available
        """
        log.debug("In: CanBus.read id:%s count:%i, block:%s" %
                  (hex(CAN_id), count, str(block)))
        while block and (len(cls.rx_buffers[CAN_id]) < count):
            pass
        log.debug("Done Blocking: CanBus.read")
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
    def write(cls, CAN_id, count=1, data, block=False):
        """
        This method is a firmware interception point for the peripheral device, 
        handling write events to the CANBus.
        """

        CanBus.tx_data(CanBus, CAN_id, data)
