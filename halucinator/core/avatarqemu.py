"""
This is the Avatar-Qemu interface for Halucinator
"""

# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

import signal
import yaml
import logging
import os
import time
import sys
from IPython import embed

from avatar2 import Avatar, QemuTarget, TargetStates
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral

from .. import arch
from ..arch import arch_package
from ..config import *
from ..config.gdb import gdb_find
from ..util import hexyaml
from ..util.profile_hals import State_Recorder
from ..util.logging import *
from .halucinator import *

from ..bp_handlers import intercepts as intercepts
from ..peripheral_models import generic as peripheral_emulators
from ..peripheral_models import peripheral_server as periph_server
from . import statistics as hal_stats



def setup_memory(avatar, name, memory, base_dir=None, record_memories=None):
    '''
        Sets up memory regions for the emualted devices
        Args:
            avatar(Avatar):
            name(str):    Name for the memory
            memory(dict): Dict from yaml config file for memory 
                          requires keys [base_addr, size] 
                          optional keys [emulate (a memory emulator), 
                          perimissions, filename]
            returns:
                permission
    '''

    filename = get_memory_backing_file(memory, base_dir)

    permissions = memory['permissions'] if 'permissions' in memory else 'rwx'
    # if 'model' in memory:
    #     emulate = getattr(peripheral_emulators, memory['emulate'])

    # #TODO, just move this to models/bp_handlers but don't want break
    # all configs right now
    if 'emulate' in memory:
        emulate = getattr(peripheral_emulators, memory['emulate'])
    else:
        emulate = None
    log.info("Adding Memory: %s Addr: 0x%08x Size: 0x%08x" %
             (name, memory['base_addr'], memory['size']))
    avatar.add_memory_range(memory['base_addr'], memory['size'],
                            name=name, file=filename,
                            permissions=permissions, emulate=emulate)

    if record_memories is not None:
        if 'w' in permissions:
            record_memories.append((memory['base_addr'], memory['size']))

# This can stay here:
def emulator_init(config, architecture, name, entry_addr, firmware=None, log_basic_blocks=False,
                    output_base_dir='', gdb_port=1234):

    # Locate binaries:
    qemu_path = qemu_find(config)
    gdb_path = gdb_find(config)

    outdir = os.path.join(output_base_dir, 'tmp', name)
    hal_stats.set_filename(outdir+"/stats.yaml")
    
    # Log emulation parameters:
    log.info("* Qemu Path = %s" % qemu_path)
    log.info("* GDB Path  = %s" % gdb_path)
    log.info("* GDB Port  = %s" % str(gdb_port))
    log.info("* Entry Address = 0x%08x" % (entry_addr))

    # LUT: QEMU_ARCH_LUT={'cortex-m3': ARMv7mQemuTarget, 'arm': ARMQemuTarget}
    # AV: architecture now sets its avatarqemu.emulator variable to the class 
    # name it uses as its Qemu class. 
    qemu_target = architecture.avatarqemu.emulator
    avatararch  = architecture.avatarqemu.resolve_avatar_cpu(config)
    # Set up Avatar:
    avatar = Avatar(arch=avatararch, output_directory=outdir)
    qemu = avatar.add_target(qemu_target,
                             gdb_executable=config["gdb_location"],
                             gdb_port=gdb_port,
                             qmp_port=gdb_port+1,
                             firmware=firmware,
                             executable=qemu_path,
                             entry_address=entry_addr, name=name)

                              # Get info from config
    
    
    if config.get("qemu_debug", False):
        qemu.log.setLevel(logging.DEBUG)

    # Extras:
    if log_basic_blocks == 'irq':
        qemu.additional_args = ['-d', 'in_asm,exec,int,cpu,guest_errors,avatar,trace:nvic*', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    elif log_basic_blocks == 'regs':
        qemu.additional_args = ['-d', 'in_asm,exec,cpu', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    elif log_basic_blocks == 'exec':
        qemu.additional_args = ['-d', 'exec', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    elif log_basic_blocks == 'trace-nochain':
        qemu.additional_args = ['-d', 'in_asm,exec,nochain', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    elif log_basic_blocks == 'trace':
        qemu.additional_args = ['-d', 'in_asm,exec', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]

    elif log_basic_blocks:
        qemu.additional_args = ['-d', 'in_asm', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    return avatar, qemu




def setup_peripheral(avatar, name, per, base_dir=None):
    '''
        Just a memory, but will usually have an emulate field. 
        May not when just want to treat peripheral as a memory
    '''
    setup_memory(avatar, name, per, base_dir)



def get_entry_and_init_sp(config, base_dir, architecture):
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

    init_memory_key = config.get('init_memory', 'flash')
    init_memory_section = config['memory_map'][init_memory_key]
    init_filename = get_memory_backing_file(init_memory_section , base_dir)

    init_sp, entry_addr = architecture.firmware.get_sp_and_entry(init_filename)
    log.info("ENTRY ADDR=%x   INIT_SP=%x", entry_addr, init_sp)
    return init_sp, entry_addr


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

    intercepts = config.get('intercepts')
    if intercepts != None:
        for intercept in intercepts:
            f_name = intercept['function']
            # Update address if in address list
            if f_name in func2addr_lut:

                if config["ARCHDEF"] == arch.Architecture.CORTEXM:
                    intercept['addr'] = (func2addr_lut[f_name] &
                                         0xFFFFFFFE)  # clear thumb bit
                else:
                    intercept['addr'] = func2addr_lut[f_name]
                log.info("Replacing address for %s with %s " %
                        (f_name, hex(func2addr_lut[f_name])))
            elif 'addr' not in intercept:
                remove_ids.append((intercept, f_name))
    else:
        log.warn("No intercepts found in configuration file.")

    config['callables'] = func2addr_lut

    for (intercept, f_name) in remove_ids:
        log.info("Removing Intercept for: %s" % f_name)
        config['intercepts'].remove(intercept)

    return base_addr, entry_addr

def emulate_binary(config, base_dir, log_basic_blocks=None,
                   gdb_port=1234, elf_file=None, db_name=None, addressfile=None):

    tx_port = config["ipc"].get("tx_port", 5556)
    rx_port = config["ipc"].get("rx_port", 5555)
    target_name = config.get("projectname", "HALucinator")

    archstring = config.get("architecture", "")
    archenum, _ = arch.arch_find(archstring)
    config["ARCHDEF"] = archenum

    if config["ARCHDEF"] == arch.Architecture.UNKNOWN:
        if archstring == "":
            log.ERROR("Architecture of project not specified. Please specify 'architecture: \"cortexm\"' in your project config yaml for default ARM Cortex-M behaviour")
        else:
            log.ERROR("Did not recognize architecture %s. Please specify a known architecture." % archstring)
        quit(1)
    
    if addressfile:
        override_addresses(config, addressfile)

    # AV TODO: this is a little bit ugly. Ideally, we would not use 
    # python modules for this, but architecture would be a class.
    # However this leaves us the flexibility to define functions and 
    # generic support across architectures, so we'll leave it 
    # alone for now.
    architecture = arch_package(config["ARCHDEF"])

    init_sp, entry_addr = get_entry_and_init_sp(config, base_dir, architecture)
    periph_server.base_dir = base_dir
    log.info("Entry Addr: 0x%08x,  Init_SP 0x%08x" % (entry_addr, init_sp))

    avatar, qemu = emulator_init(config, 
                                 architecture,
                                 target_name,
                                 entry_addr,
                                 log_basic_blocks=log_basic_blocks,
                                 output_base_dir=base_dir, 
                                 gdb_port=gdb_port)

    if 'options' in config:
        log.info("Config file has options")
        if 'remove_bitband' in config['options'] and \
                config['options']['remove_bitband']:
            log.info("Removing Bitband")
            qemu.remove_bitband = True

    # Setup Memo/bry Regions
    record_memories = []
    for name, memory in list(config['memory_map'].items()):
        setup_memory(avatar, name, memory, base_dir, record_memories)

    # Add memory needed for returns
    architecture.avatarqemu.add_patch_memory(avatar)

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

    # Setup Peripherals' Regions
    peripherallist = config.get('peripherals')
    if peripherallist != None:
        peripherals = list(peripherallist.items())
        for name, per in peripherals:
            # They are just memories
            setup_peripheral(avatar, name, per, base_dir)
    else:
        log.warn("No peripherals configured in config file.")

    # Setup Intercept MMIO Regions
    added_classes = []

    interceptlist = config.get('intercepts', [])
    print(interceptlist)
    if interceptlist:
        for intercept in interceptlist:
            log.info("Intercept: Intercept Memory Configuration %s" % (intercept["function"]))
            bp_cls = intercepts.get_bp_handler(intercept)
            
            if bp_cls == None:
                log.error("Unable to find intercept class %s for %s" % (intercept["class"], intercept["functin"]))
            
            if issubclass(bp_cls.__class__, AvatarPeripheral):
                name, addr, size, per = bp_cls.get_mmio_info()
                if bp_cls not in added_classes:
                    log.info("Adding Memory Region for %s, (Name: %s, Addr: %s, Size:%s)"
                            % (bp_cls.__class__.__name__, name, hex(addr), hex(size)))
                    avatar.add_memory_range(addr, size, name=name, permissions=per,
                                            forwarded=True, forwarded_to=bp_cls)
                    added_classes.append(bp_cls)
    else:
        log.warn("No intercepts found in configuration file.")
   
    # Setup Intecepts
    avatar.watchmen.add_watchman('BreakpointHit', 'before',
                                 intercepts.interceptor, is_async=True)
    avatar.watchmen.add_watchman('SigTrapHit', 'before', 
                                 intercepts.traphandler, is_async=True)
    qemu.gdb_port = gdb_port

    avatar.callables = config['callables']
    avatar.init_targets()

    if interceptlist:
        for intercept in interceptlist:
            
            bp_classname = intercept.get("class")
            bp_funcname  = intercept.get("function")
            
            log.info("Intercept: Wiring up intercept for %s to %s " % (bp_funcname, bp_classname))
            
            bp_cls = intercepts.get_bp_handler(intercept)

            if bp_cls == None:
                log.error("Unable to find intercept class %s for %s" % (intercept["class"], intercept["functin"]))

            intercepts.register_bp_handler(qemu, intercept)

            

    qemu.init_sp = init_sp
    architecture.avatarqemu.arch_specific_setup(config, qemu)
    architecture.avatarqemu.write_patch_memory(qemu)
    

    def signal_handler(signum,frame):
        
        pid = os.getpid()
        print("Process %d: Received Signal %d, shutting down." % (pid, signum))
            
        if pid != periph_server.ppid:
            print("Process %d: Shutdown Complete." % (pid,))
            quit(0)
        
        print("Process %d: Shutting down emulators." % (pid,))
        periph_server.stop()
        time.sleep(1) 
        avatar.stop()
        avatar.shutdown()
        print("Process %d: Shutdown Complete." % (pid,))
        #except:
        #    pass
        quit(0)
    
    # Try to tidy up nicely if: Killed (SIGKILL), interrupted (ctrl+c) or 
    # user closes controlling terminal (Hang-up HUP).
    signal.signal(signal.SIGINT, signal_handler)
    #signal.signal(signal.SIGKILL, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    
    # Emulate the Binary
    periph_server.start(rx_port, tx_port, qemu)
    

    # import os; os.system('stty sane') # Make so display works
    # import IPython; IPython.embed()
    qemu.cont()
    
    periph_server.run_server()

class AvatarQemuRehost(HalucinatorRehost):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        


