# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from .peripheral import requires_tx_map, requires_rx_map, requires_interrupt_map
from . import peripheral_server
from collections import defaultdict

import logging
log = logging.getLogger("gpio")
# Register the pub/sub calls and methods that need mapped
@peripheral_server.peripheral_model
class MMIOLed(object):

    hal_name = ""
    hal_value = 0
    hal_size = 1
    hal_endianness = 'little'

    def __init__(self, name='undefined', initial_value=0, max_size=1, endianness='little', **kwargs):
        if name == 'undefined':
            raise Exception("Peripheral is not named.")
        self.hal_name = name
        self.hal_value = initial_value
        self.hal_size = max_size

    @peripheral_server.tx_msg
    def model_write(self, offset, value, size):
        '''
            Creates the message that peripheral_server.tx_msg will send on this 
            event
        '''
        if size < 0:
            raise Exception("Avatar Bug")
        if size > self.hal_size - offset:
            raise Exception("OOB Write")

        self.hal_value = (int.from_bytes(value, self.endianness)) << offset
        msg = {name: self.hal_name, value: self.hal_value}
        log.debug("MMIOLED.Write " + repr(msg))
        return msg

    @peripheral_server.reg_rx_handler
    def model_ext_memory_change(self, msg):
        '''
            Processes reception of messages from external 0mq server
            type is GPIO.zmq_set_gpio
        '''
        print("MMIOLED.External_Change", msg)
        name = msg['name']
        value = msg['value']
        self.hal_value = value

    def model_read(self, offset, size):
        if size < 0:
            raise Exception("Avatar Bug")
        if size > self.hal_size - offset:
            raise Exception("OOB Read")
        valueasbytes = self.value.to_bytes(max_size, endianness)
        return valueasbytes[offset:size]
