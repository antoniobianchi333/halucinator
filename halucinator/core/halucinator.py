# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

import signal
import yaml
import logging
import os
import time
import sys

from avatar2 import Avatar, QemuTarget, ARM_CORTEX_M3, TargetStates
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral

from IPython import embed

from ..util import hexyaml
from ..peripheral_models import generic as peripheral_emulators
from ..bp_handlers import intercepts as intercepts
from ..peripheral_models import peripheral_server as periph_server
from ..util.profile_hals import State_Recorder
from ..util import cortex_m_helpers as CM_helpers
from . import hal_stats


log = logging.getLogger("Halucinator")
log.setLevel(logging.DEBUG)
avalog = logging.getLogger("avatar")
avalog.setLevel(logging.WARN)
pslog = logging.getLogger("PeripheralServer")
pslog.setLevel(logging.WARN)
# log.setLevel(logging.DEBUG)


QemuTarget.trigger_interrupt = trigger_interrupt
QemuTarget.set_vector_table_base = set_vector_table_base
# --------------------------END QemuTarget Hack --------------------------------


def python_version_check():

    major, minor = sys.version_info.major, sys.version_info.minor

    if major < 3 or (major == 3 and minor <= 5):
        print("Python version 3.5 or later required, version %d.%d detected" % (major, minor))
        return False

    return True

def setup_peripheral(avatar, name, per, base_dir=None):
    '''
        Just a memory, but will usually have an emulate field. 
        May not when just want to treat peripheral as a memory
    '''
    setup_memory(avatar, name, per, base_dir)



def get_entry_and_init_sp(config, base_dir):
    '''
    Gets the entry point and the initial SP.
    This is a work around because AVATAR-QEMU does not init Cortex-M3
    correctly. 

    Works by identifying the init_memory, and reading the reset vector from
    the file loaded into it memory.
    Args:
        config(dict):   Dictionary of config file(yaml)
    avatar.add_memory_range(0xB000_00000, memory['size'], 
                            name=name, file=filename, 
                            permissions=permissions, emulate=emulate)
    avatar.add_memory_range(0xB000_00000, memory['size'], 
                            name=name, file=filename, 
                            permissions=permissions, emulate=emulate)ion
    avatar.add_memory_range(0xB000_00000, memory['size'], 
                            name=name, file=filename, 
                            permissions=permissions, emulate=emulate)ointer
    avatar.add_memory_range(0xB000_00000, memory['size'], 
                            name=name, file=filename, 
                            permissions=permissions, emulate=emulate)
    '''

    init_memory = config['init_memory'] if 'init_memory' in config else 'flash'
    init_filename = get_memory_filename(
        config['memories'][init_memory], base_dir)

    init_sp, entry_addr, = CM_helpers.get_sp_and_entry(init_filename)
    return init_sp, entry_addr


def emulate_binary(config, base_dir, target_name=None, log_basic_blocks=None,
                   rx_port=5555, tx_port=5556, gdb_port=1234, elf_file=None, db_name=None):

    init_sp, entry_addr = get_entry_and_init_sp(config, base_dir)
    periph_server.base_dir = base_dir
    log.info("Entry Addr: 0x%08x,  Init_SP 0x%08x" % (entry_addr, init_sp))

    avatar, qemu = get_qemu_target(target_name, entry_addr,
                                   log_basic_blocks=log_basic_blocks,
                                   output_base_dir=base_dir, gdb_port=gdb_port)

    if 'options' in config:
        log.info("Config file has options")
        if 'remove_bitband' in config['options'] and \
                config['options']['remove_bitband']:
            log.info("Removing Bitband")
            qemu.remove_bitband = True

    # Setup Memory Regions
    record_memories = []
    for name, memory in list(config['memories'].items()):
        setup_memory(avatar, name, memory, base_dir, record_memories)

    # Add memory needed for returns
    add_patch_memory(avatar, qemu)

    # Add recorder to avatar
    # Used for debugging peripherals
    if elf_file is not None:
        if db_name is None:
            db_name = ".".join((os.path.splitext(elf_file)[
                               0], str(target_name), "sqlite"))
        avatar.recorder = State_Recorder(
            db_name, qemu, record_memories, elf_file)
    else:
        avatar.recorder = None

    # Setup Peripherals Regions
    for name, per in list(config['peripherals'].items()):
        # They are just memories
        setup_peripheral(avatar, name, per, base_dir)

    # Setup Intercept MMIO Regions
    added_classes = []
    for intercept in config['intercepts']:
        bp_cls = intercepts.get_bp_handler(intercept)
        if issubclass(bp_cls.__class__, AvatarPeripheral):
            name, addr, size, per = bp_cls.get_mmio_info()
            if bp_cls not in added_classes:
                log.info("Adding Memory Region for %s, (Name: %s, Addr: %s, Size:%s)"
                         % (bp_cls.__class__.__name__, name, hex(addr), hex(size)))
                avatar.add_memory_range(addr, size, name=name, permissions=per,
                                        forwarded=True, forwarded_to=bp_cls)
                added_classes.append(bp_cls)
   # Setup Intecepts
    avatar.watchmen.add_watchman('BreakpointHit', 'before',
                                 intercepts.interceptor, is_async=True)
    qemu.gdb_port = gdb_port

    avatar.callables = config['callables']
    avatar.init_targets()

    for intercept in config['intercepts']:
        intercepts.register_bp_handler(qemu, intercept)

    # Work around Avatar-QEMU's improper init of Cortex-M3
    qemu.regs.cpsr |= 0x20  # Make sure the thumb bit is set
    qemu.regs.sp = init_sp  # Set SP as Qemu doesn't init correctly
    # TODO Change to be read from config
    qemu.set_vector_table_base(0x08000000)
    write_patch_memory(qemu)

    def signal_handler(a,b):
        #try:
        log.info("Received Ctrl+C, shutting down.")
        periph_server.stop()
        avatar.stop()
        avatar.shutdown()
        log.info("Shutdown Complete.")
        #except:
        #    pass
        quit(0)
    
    signal.signal(signal.SIGINT, signal_handler)

    # Emulate the Binary
    periph_server.start(rx_port, tx_port, qemu)
    # import os; os.system('stty sane') # Make so display works
    # import IPython; IPython.embed()
    qemu.cont()

    try:
        periph_server.run_server()
        # while 1:

        #    time.sleep(0.5)
    except KeyboardInterrupt:
        # import os; os.system('stty sane') # Make so display works
        # import IPython; IPython.embed()
        periph_server.stop()
        avatar.stop()
        avatar.shutdown()
        quit(-1)


def override_addresses(config, address_file):
    '''
        Replaces address in config with address from the address_file with same
        function name
    '''
    with open(address_file, 'rb') as infile:
        addr_config = yaml.load(infile, Loader=yaml.FullLoader)
        addr2func_lut = addr_config['symbols']
        func2addr_lut = {}
        for key, val in list(addr2func_lut.items()):
            func2addr_lut[val] = key
        base_addr = addr_config['base_address']
        entry_addr = addr_config['entry_point']

    remove_ids = []
    for intercept in config['intercepts']:
        f_name = intercept['function']
        # Update address if in address list
        if f_name in func2addr_lut:
            intercept['addr'] = (func2addr_lut[f_name] &
                                 0xFFFFFFFE)  # clear thumb bit
            log.info("Replacing address for %s with %s " %
                     (f_name, hex(func2addr_lut[f_name])))
        elif 'addr' not in intercept:
            remove_ids.append((intercept, f_name))

    config['callables'] = func2addr_lut

    for (intercept, f_name) in remove_ids:
        log.info("Removing Intercept for: %s" % f_name)
        config['intercepts'].remove(intercept)

    return base_addr, entry_addr

class HalucinatorRehost(object):

	def __init__(self):
		pass
