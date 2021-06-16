

from collections import deque, defaultdict
import logging
import cmd2
import zmq
from ..peripheral_models.peripheral_server import encode_zmq_msg, decode_zmq_msg
from .ioserver import IOServer

log = logging.getLogger("LEDDevice")

class LEDDevice(object):

    handled_instances = []
    vcallback = None

    def __init__(self, ioserver, names, values_callback=None):
        self.ioserver = ioserver
        self.vcallback = values_callback
        handled_names = names
        for name in names:
            topic = 'Peripheral.MMIOLED.%s.write' % (name)
            log.debug("Registering for ZMQ Topic: %s" % (topic))
            self.ioserver.register_topic(
                topic,
                self.tx_handler)

    def rx_handler(self, name, msg):
        """
        Peripheral Server -> Emulator (emulated device receives)
        """
        topic = 'Peripheral.MMIOLED.%s.write' % (name)
        self.ioserver.send_msg(topic, msg)
        return

    def tx_handler(self, io_server, msg):
        name = msg['name']
        value = msg['value']
        
        if self.values_callback:
            vcallback(name, value)

