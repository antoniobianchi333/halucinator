# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

import logging
from ...peripheral_models.mmioled import MMIOLed
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral


log = logging.getLogger("MMIO.LED")
log.setLevel(logging.DEBUG)


class GenericPeripheral(AvatarPeripheral, MMIOLed):
     
    def __init__(self, name, address, size, **kwargs):
        AvatarPeripheral.__init__(self, name, address, size)
        MMIOLed.__init__()

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write

        # TODO: why is 10 hardcoded here:
        log.info("Setting Handlers %s" % str(self.read_handler[0:10]))

    def hw_read(self, offset, size, pc=0xBAADBAAD):
        self.model_read(offset, size)
        return ret

    def hw_write(self, offset, size, value, pc=0xBAADBAAD):
        self.model_write(offset, size, value) 
        return True




