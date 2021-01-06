# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from os import sys, path
from ...peripheral_models.rs232 import SerialPublisher
from ..bp_handler import BPHandler, bp_handler
import logging
log = logging.getLogger("AVR8SERIAL")
log.setLevel(logging.DEBUG)

class AVR8SERIAL(BPHandler):

    def __init__(self, impl=SerialPublisher):
        self.model = impl


    @bp_handler(['_ZN14HardwareSerial9availableEv'])
    def handle_status(self, qemu, bp_addr):
        log.info("Handle Available Status Requested, Returning True")
        return True, 0

    @bp_handler(['_ZN14HardwareSerial17availableForWriteEv'])
    def handle_write_status(self, qemu, bp_addr):
        log.info("Handle Write Status Requested, Returning True")
        return True, 0


    @bp_handler(['_ZN14HardwareSerial5writeEh'])
    def handle_write(self, qemu, bp_addr):
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
        
        self.model.write(string_str)
        return True, 1

    @bp_handler(['_ZN14HardwareSerial5flushEv'])
    def handle_flush(self, qemu, bp_addr):
        return True, 1

    @bp_handler(['_ZN14HardwareSerial4readEv', 
                 '_ZN14HardwareSerial4peekEv',
                 '_ZN14HardwareSerial17_tx_udr_empty_irqEv'])
    def handle_other(self, qemu, bp_addr):
        return True, 0


