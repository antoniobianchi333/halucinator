# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

import logging
from ...peripheral_models.mmioled import MMIOLed
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral


log = logging.getLogger("MMIO.LED")
log.setLevel(logging.DEBUG)


class MMIOLedPeripheral(AvatarPeripheral, MMIOLed):
     
    def __init__(self, name, address, size, **kwargs):
        AvatarPeripheral.__init__(self, name, address, size)
        MMIOLed.__init__(self, name=name, initial_value=0, max_size=size)

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write

        log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.read_handler[0:size])))
        log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.write_handler[0:size])))

    def hw_read(self, offset, size, pc=0xBAADBAAD):
        log.info("READ %s %d+%d", self.hal_name, offset, size)
        self.model_read(offset, size)
        return ret

    def hw_write(self, offset, size, value, pc=0xBAADBAAD):
        log.info("WRITE %s %d+%d", self.hal_name, offset, size)
        self.model_write(offset, size, value) 
        return True




