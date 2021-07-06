
from collections import deque, defaultdict
import logging
import cmd2
import zmq
import json
from ..peripheral_models.peripheral_server import encode_zmq_msg, decode_zmq_msg
from .ioserver import IOServer

log = logging.getLogger("LEDDevice")
log.setLevel(logging.DEBUG)

class LEDDevice(object):


    def __init__(self, ioserver, led_names, notify_handler):
        self.ioserver = ioserver
        for name in led_names:
            self.ioserver.register_topic(
                'Peripheral.LED.%s.write' % (name),
                self.tx_handler)
        self.notify_handler = notify_handler

    def rx_handler(self, idx, msg):
        """ 
        Peripheral Server -> Emulator (emulated device receives)
        Here we send messages to the IO Server 
        """
        pass
    
    def tx_handler(self, ioserver, msg):
        """ 
        Emulator -> Peripheral Server emulated device sends)
        Here we handle messages received from the virtual peripheral.
        We don't transmit here, the naming matches peripheral_models.
        """
        name  = msg['name']
        value = msg['value']
        
        self.notify_handler(name, value)
