# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from . import peripheral_server
#from queue import Queue
from threading import Event, Thread
#from collections import deque, defaultdict
import sys
import logging
from itertools import repeat
import time

log = logging.getLogger("RS232Model")
log.setLevel(logging.DEBUG)

# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class SerialPublisher(object):
    rx_buffer = list()

    @classmethod
    @peripheral_server.tx_msg
    def write(cls, data):
        '''
           Publishes the data to sub/pub server
        '''
        log.debug("In: RS232Publisher.write: %s" % data)
        msg = {'data': data}
        return msg

    @classmethod
    def read(cls, count, block=False):
        '''
            Gets data previously received from the sub/pub server
            Args:
                count:  Max number of chars to read
                block(bool): Block if data is not available
        '''
        log.debug("In: RS232Publisher.read block:%s" %
                  (str(block)))
        while block and (len(cls.rx_buffer) < count):
            pass

        
        log.debug("Done Blocking: SerialPublisher.read")
        
        chars_available = len(buffer)
        if chars_available >= count:
            chars = [clx.rx_buffer.popleft() for _ in range(count)]
            chars = ''.join(chars).encode('utf-8')
        else:
            chars = [cls.rx_buffer.popleft() for _ in range(chars_available)]
            chars = ''.join(chars).encode('utf-8')

        return chars

    @classmethod
    @peripheral_server.reg_rx_handler
    def rx_data(cls, msg):
        '''
            Handles reception of these messages from the PeripheralServer
        '''
        log.debug("rx_data got message: %s" % str(msg))
        data = msg['data']
        cls.rx_buffer.append(data)
