# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from os import sys, path
from ...peripheral_models.uart import UARTPublisher
from ..bp_handler import BPHandler, bp_handler
import logging
log = logging.getLogger("STM32F4UART")
log.setLevel(logging.DEBUG)


class AVR8SERIAL(BPHandler):

    def __init__(self, impl=UARTPublisher):
        self.model = impl


    @bp_handler(['_ZN14HardwareSerial5writeEh'])
    def handle_tx(self, qemu, bp_addr):
        '''
            Reads the frame out of the emulated device, returns it and an 
            id for the interface(id used if there are multiple ethernet devices)
        '''
        string_low = qemu.regs.r24
        string_high = qemu.regs.r25
        string_ptr = (string_low | string_high << 8)

        # TODO: C-string read until 0
        strbytes = []
        while True:
            byte = qemu.read_memory(string_ptr, 1, 1)
            strbytes.append(byte)
            if byte == 0:
                break

        string_bytes = bytes(strbytes)
        string_str = string_bytes.decode("utf-8")
    
        log.info("Writing: %s" % string_str)
        
        self.model.write(hw_addr, string_str)
        return True, 0


