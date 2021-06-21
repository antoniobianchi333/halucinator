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

log = logging.getLogger("AMP")
log.setLevel(logging.DEBUG)




# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class AMP(object):

    data_value = None

    @classmethod
    @peripheral_server.reg_rx_handler
    def rx_data(cls, msg):
        """
        Peripheral Server -> Emulator
        This method receives data send from the peripheral device and buffers 
        it for intercepts of the read method.
        """
        # {'data': [0, 0, 0, 128, 12, 0, 0, 0], 'id': 16707840}
        log.debug("rx_data got message: %s" % str(msg))
        data = msg['data']
        cls.data_value = data 

