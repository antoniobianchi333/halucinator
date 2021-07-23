# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from avatar2.peripherals.avatar_peripheral import AvatarPeripheral
from ..core import statistics as hal_stats
import logging

from .peripheral_server import zmq_encode_and_send

log = logging.getLogger("GenericPeripheral")
log.setLevel(logging.DEBUG)

hal_stats.stats['MMIO_read_addresses'] = set()
hal_stats.stats['MMIO_write_addresses'] = set()
hal_stats.stats['MMIO_addresses'] = set()
hal_stats.stats['MMIO_addr_pc'] = set()

#
# led_left_outer: {base_addr: 0x40000034, size: 0x04, permissions: rw-, emulate: MMIOLedPeripheral}
# led_left_inner: {base_addr: 0x40000038, size: 0x04, permissions: rw-, emulate: MMIOLedPeripheral}
# led_right_inner: {base_addr: 0x40000040, size: 0x04, permissions: rw-, emulate: MMIOLedPeripheral}
# led_right_outer: {base_addr: 0x40002034, size: 0x04, permissions: rw-, emulate: MMIOLedPeripheral}


led_left_outer = 0x40000034
led_left_inner = 0x40000038
led_right_inner = 0x40000040
led_right_outer = 0x40002034

class GenericPeripheral(AvatarPeripheral):
    read_addresses = set()

    def hw_read(self, offset, size, pc=0xBAADBAAD):
        log.info("%s: Read from addr, 0x%08x size %i, pc: %s" %
                 (self.name, self.address + offset, size, hex(pc)))
        addr = self.address + offset
        hal_stats.write_on_update('MMIO_read_addresses', hex(addr))
        hal_stats.write_on_update('MMIO_addresses', hex(addr))
        hal_stats.write_on_update(
            'MMIO_addr_pc', "0x%08x,0x%08x,%s" % (addr, pc, 'r'))

        ret = 0
        return ret

    def hw_write(self, offset, size, value, pc=0xBAADBAAD):
        log.info("%s: Write to addr: 0x%08x, size: %i, value: 0x%08x, pc %s" % (
            self.name, self.address + offset, size, value, hex(pc)))
        addr = self.address + offset
        
        hal_stats.write_on_update('MMIO_write_addresses', hex(addr))
        hal_stats.write_on_update('MMIO_addresses', hex(addr))
        hal_stats.write_on_update(
            'MMIO_addr_pc', "0x%08x,0x%08x,%s" % (addr, pc, 'w'))

        msg = None
        if addr == led_left_outer:
            msg = {'name': 'led_left_outer', 'value': value}
            topic = 'Peripheral.LED.led_left_outer.write'
        elif addr == led_left_inner:
            msg = {'name': 'led_left_inner', 'value': value}
            topic = 'Peripheral.LED.led_left_inner.write'
        elif addr == led_right_inner:
            msg = {'name': 'led_right_inner', 'value': value}
            topic = 'Peripheral.LED.led_right_inner.write'
        elif addr == led_right_outer:
            msg = {'name': 'led_right_outer', 'value': value}
            topic = 'Peripheral.LED.led_right_outer.write'
        else:
            pass
       
        
        if msg:
            log.info("******** SEND MESSAGE")
            zmq_encode_and_send(topic, msg)
        return True

    def __init__(self, name, address, size, **kwargs):
        AvatarPeripheral.__init__(self, name, address, size)

        self.read_handler[0:size] = self.hw_read
        self.write_handler[0:size] = self.hw_write

        log.info("Setting Handlers %s" % str(self.read_handler[0:10]))


