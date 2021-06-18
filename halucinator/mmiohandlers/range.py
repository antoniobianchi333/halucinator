# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

import logging
from ..peripheral_models.mmioled import MMIOLed
from ..core import statistics as hal_stats
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral

log = logging.getLogger("RangePeripheral")
log.setLevel(logging.DEBUG)

hal_stats.stats['MMIO_read_addresses'] = set()
hal_stats.stats['MMIO_write_addresses'] = set()
hal_stats.stats['MMIO_addresses'] = set()
hal_stats.stats['MMIO_addr_pc'] = set()


class MMIOPeripheral(AvatarPeripheral):
    read_addresses = set()

    def hw_read_log(self, offset, size, pc=0xBAADBAAD):
        log.info("%s: Read from addr, 0x%08x size %i, pc: %s" %
                 (self.name, self.address + offset, size, hex(pc)))
        addr = self.address + offset
        hal_stats.write_on_update('MMIO_read_addresses', hex(addr))
        hal_stats.write_on_update('MMIO_addresses', hex(addr))
        hal_stats.write_on_update(
            'MMIO_addr_pc', "0x%08x,0x%08x,%s" % (addr, pc, 'r'))

        ret = 0
        return ret

    def hw_write_log(self, offset, size, value, pc=0xBAADBAAD):
        log.info("%s: Write to addr: 0x%08x, size: %i, value: 0x%08x, pc %s" % (
            self.name, self.address + offset, size, value, hex(pc)))
        addr = self.address + offset
        hal_stats.write_on_update('MMIO_write_addresses', hex(addr))
        hal_stats.write_on_update('MMIO_addresses', hex(addr))
        hal_stats.write_on_update(
            'MMIO_addr_pc', "0x%08x,0x%08x,%s" % (addr, pc, 'w'))
        return True
    
    def hw_read_redirect(self, offset, size, pc=0xBAADBAAD):
        log.info("READ %s %d+%d", self.hal_name, offset, size)
        ret = self.model.model_read(offset, size)
        return ret

    def hw_write_redirect(self, offset, size, value, pc=0xBAADBAAD):
        log.info("WRITE %s %d+%d", self.hal_name, offset, size)
        self.model.model_write(offset, size, value) 
        return True

    def __init__(self, name, address, size, **kwargs):
        AvatarPeripheral.__init__(self, name, address, size)
        
        self.model = MMIOLed(name=name, initial_value=0, max_size=size)

        self.ranges = kwargs.get('hal_ranges')
        print(self.ranges)
        for memrange in self.ranges:

            begin = memrange['offset']
            rsize  = memrange['size']
            action = memrange['action']

            if action == 'log':
                self.read_handler[begin:begin+rsize] = self.hw_read_log
                self.write_handler[begin:begin+rsize] = self.hw_write_log

                log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.read_handler[begin:begin+rsize])))
                log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.write_handler[begin:begin+rsize])))
            elif action == 'model':
                self.read_handler[begin:begin+rsize] = self.hw_read_redirect
                self.write_handler[begin:begin+rsize] = self.hw_write_redirect

                log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.read_handler[begin:begin+rsize])))
                log.info("Setting Handlers for 0x%08x = %s" % (address, str(self.write_handler[begin:begin+rsize])))


