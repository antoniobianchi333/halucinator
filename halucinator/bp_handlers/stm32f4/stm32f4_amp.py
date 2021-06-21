# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from ...peripheral_models.interrupts import Interrupts
from ...peripheral_models.amp import AMP
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral
from ..intercepts import tx_map, rx_map
from ..bp_handler import BPHandler, bp_handler
import time
from collections import defaultdict

import queue
import logging

log = logging.getLogger("STM32F4_AMP")
log.setLevel(logging.INFO)

class STM32_AMP(BPHandler):

    def __init__(self, model=AMP):
        self.model = model
        self.name = 'AMP'

    @bp_handler(['_Z16rx_brake_routinePhP6Bumper'])
    def handle_rx(self, qemu, bp_addr):
        can_dashclass = qemu.regs.r1
        
        log.info("rx_brake_routine entered, seeing if we should modify r1")
        r1data = self.model.data_value
        if r1data == None:
            return False, 0

        offset = -1
        value = None
        idx = 0
        for r1v in r1data:
            if r1v != None:
                offset = idx
                value = r1v

        if value == None:
            return False, 0

        # write_memory(self, address, wordsize, val, num_words=1, raw=False)
        qemu.write_memory(can_dashclass, 1, value, 1)
        log.info("rx_brake_routine: r1 patched.")
        return False, 0
