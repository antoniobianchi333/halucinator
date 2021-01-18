# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from os import sys, path
from ...peripheral_models.rs232 import RS232Publisher
from ..bp_handler import BPHandler, bp_handler
import logging
log = logging.getLogger("AVR8SERIAL")
log.setLevel(logging.DEBUG)
    
SERIAL_BUFFER_SIZE = 255

class AVR8SERIAL(BPHandler):


    def __init__(self, impl=RS232Publisher):
        self.model = impl
        self.buffer_head = 0

    @bp_handler(['_ZN14HardwareSerial9availableEv'])
    def handle_status(self, qemu, bp_addr):
        log.info("Handle Available Status Requested, Returning True")

        return True, SERIAL_BUFFER_SIZE

    @bp_handler(['_ZN14HardwareSerial17availableForWriteEv'])
    def handle_write_status(self, qemu, bp_addr):
        log.info("Handle Write Status Requested, Returning True")
        return True, SERIAL_BUFFER_SIZE - 1 + (self.buffer_head)

    # Arduino code does not flush immediately. We will, and just track 
    # what we are allegedly buffering, which is reset on flush.
    @bp_handler(['_ZN14HardwareSerial5writeEh'])
    def handle_write(self, qemu, bp_addr):
        log.info("Handle Write Requested.")
        '''
            Reads the frame out of the emulated device, returns it and an 
            id for the interface(id used if there are multiple ethernet devices)
        '''


        sram_addr_low  = qemu.regs.r24
        sram_addr_high = qemu.regs.r29

        sram = (sram_addr_low | sram_addr_high << 8) + 0x800100

        log.info("Possible BBBB %x" % sram)
        data_byte = qemu.read_memory(sram+0x16, 1, 1)
        log.info("BBBB Writing: %x" % data_byte)

        self.model.write(data_byte)
        self.buffer_head += 1
        return True, 1

    @bp_handler(['_ZN14HardwareSerial5flushEv'])
    def handle_flush(self, qemu, bp_addr):
        log.info("Handle Flush Requested.")
        self.buffer_head = 0
        return True, 1

    @bp_handler(['_ZN14HardwareSerial4readEv', 
                 '_ZN14HardwareSerial4peekEv',
                 '_ZN14HardwareSerial17_tx_udr_empty_irqEv'])
    def handle_other(self, qemu, bp_addr):
        log.info("Handle OTHER Requested.")
        return True, 0


