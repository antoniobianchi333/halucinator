# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from functools import wraps

import importlib
import yaml
import os
import logging

from ..util import hexyaml
from ..core import statistics as hal_stats
from . import bp_handler as bp_handler
from .. import arch as arch

from ..arch.cortexm.avatarqemu import ARMv7mQemuTarget
from ..arch.avr8.avatarqemu import AVRQemuTarget

log = logging.getLogger("Intercepts")
log.setLevel(logging.DEBUG)


hal_stats.stats['used_intercepts'] = set()


def tx_map(per_model_funct):
    '''
        Decorator that maps this function to the peripheral model that supports
        it. It registers the intercept and calls the
        Usage:  @intercept_tx_map(<PeripheralModel.method>, ['Funct1', 'Funct2'])

        Args:
            per_model_funct(PeripheralModel.method):  Method of child class that
                this method is providing a mapping for
    '''
    print("In: intercept_tx_map", per_model_funct)

    def intercept_decorator(func):
        print("In: intercept_decorator", func)
        @wraps(func)
        def intercept_wrapper(self, qemu, bp_addr):
            bypass, ret_value, msg = func(self, qemu, bp_addr)
            log.debug("Values:", msg)
            per_model_funct(*msg)
            return bypass, ret_value
        return intercept_wrapper
    return intercept_decorator


def rx_map(per_model_funct):
    '''
        Decorator that maps this function to the peripheral model that supports
        it. It registers the intercept and calls the
        Usage:  @intercept_rx_map(<PeripheralModel.method>, ['Funct1', 'Funct2'])

        Args:
            per_model_funct(PeripheralModel.method):  Method of child class that
                this method is providing a mapping for
    '''
    print("In: intercept_rx_map", per_model_funct)

    def intercept_decorator(func):
        print("In: intercept_decorator", func)
        @wraps(func)
        def intercept_wrapper(self, qemu, bp_addr):
            models_inputs = per_model_funct()
            return func(self, qemu, bp_addr, *models_inputs)
        return intercept_wrapper
    return intercept_decorator


def bp_return(qemu, bypass, ret_value):
    '''
        Handles returning from breakpoint for ARMv7-M devices
        Args:
            bypass(bool):  If true bypasses execution of the function
            ret_value(bool): The return value to provide for the execution
    '''
    print("Intercept Return: ", (bypass, ret_value))
    return
    if ret_value != None:
        # Puts ret value in r0
        qemu.regs.r0 = ret_value
    if bypass:
        # Returns from function, by putting LR in PC
        qemu.regs.pc = qemu.regs.lr
        #log.info("Executing BX LR")
        # qemu.exec_bxlr()


initalized_classes = {}
bp2handler_lut = {}
bp2handler_addr2bp = {}

def get_bp_handler(intercept_desc):
    '''
        gets the bp_handler class from the config file class name.
        Instantiates it if has not been instantiated before if 
        has it just returns the instantiated instance
    '''
    split_str = intercept_desc['class'].split('.')

    module_str = ".".join(split_str[:-1])
    class_str = split_str[-1]
    module = importlib.import_module(module_str)

    cls_obj = getattr(module, class_str)
    if cls_obj in initalized_classes:
        bp_class = initalized_classes[cls_obj]
    else:
        if 'class_args' in intercept_desc and intercept_desc['class_args'] != None:
            print('Class:', cls_obj)
            print('Class Args:', intercept_desc['class_args'])
            bp_class = cls_obj(**intercept_desc['class_args'])
        else:
            bp_class = cls_obj()
        initalized_classes[cls_obj] = bp_class
    return bp_class


def register_bp_handler(qemu, intercept_desc):
    '''
    '''

    archpkg = arch.arch_packagestring(qemu.architecture())
    bp_cls = get_bp_handler(intercept_desc)

    bpaddress = 0
    try:
        bpaddress = int(intercept_desc['addr'])
    except Exception as e:
        raise e

    function = intercept_desc['function']

    log.info("Configuring breakpoint for %s @ %x", function, bpaddress)

    # Clear thumb bit
    if isinstance(qemu, ARMv7mQemuTarget):
        log.debug("Clearing Thumb Bit on Address")
        bpaddress = bpaddress & 0xFFFFFFFE

    if isinstance(qemu, AVRQemuTarget):
        # AVR has the concept of word-based addressing (and this is how QEMU 
        # emulates it.
        bpaddress = bpaddress * 2


    if 'registration_args' in intercept_desc and \
       intercept_desc['registration_args'] != None:
        handler = bp_cls.register_handler(bpaddress,
                                          intercept_desc['function'],
                                          **intercept_desc['registration_args'])
    else:
        handler = bp_cls.register_handler(bpaddress,
                                          intercept_desc['function'])

    log.info("Registering BP Handler: %s.%s : %s" % (
        intercept_desc['class'], intercept_desc['function'], hex(bpaddress)))

    bp = qemu.set_breakpoint(bpaddress)

    if bp < 0:
        log.error("Setting breakpoint for func %s at %s failed." % (intercept_desc["function"], bpaddress))
        return

    hal_stats.stats[bp] = dict(intercept_desc)
    hal_stats.stats[bp]['count'] = 0
    hal_stats.stats[bp]['method'] = handler.__name__

    bp2handler_lut[bp] = (bp_cls, handler)
    bp2handler_addr2bp[bpaddress] = bp

    log.info("BREAKPOINT %d for func %s @ %s set." % (
        bp, intercept_desc["function"], hex(int(bpaddress))
    ))


# Interceptor handles breakpoints from the avatar watchman configured to 
# use it here. Specifically, it handles BreakpointHitMessage types, which have 
# three parameters:
# .address = where the breakpoint occurred.
# .breakpoint_number = the number assigned via the GDB protocol
# .origin = the origin inside avatar2, in this case the qemu emulator.
# This function references bp2handler_lut, which maps breakpoint numbers to 
# breakpoint handlers.
def interceptor(avatar, message):
    '''
        Callback for Avatar2 break point watchman.  It then dispatches to
        correct handler
    '''

    bp = int(message.breakpoint_number)
    qemu = message.origin
    archpkg = arch.arch_packagestring(qemu.architecture())

    if len(bp2handler_lut.items()) == 0:

        # We have no interrupt handlers. 
        # The only thing we can do is continue the VM
        qemu.cont()
        return


    if isinstance(qemu, ARMv7mQemuTarget):
        # TODO: THUMB bit make generic.
        pc = qemu.regs.pc & 0xFFFFFFFE  # Clear Thumb bit
    elif isinstance(qemu, AVRQemuTarget):
        pc = qemu.regs.pc
    else:
        raise Exception("Not Implemented")

    try:
        cls, method = bp2handler_lut[bp]
    except KeyError:
        log.exception("Unable to find handler for %8x" % bp)
        qemu.cont()
        return

    hal_stats.stats[bp]['count'] += 1
    hal_stats.write_on_update(
        'used_intercepts', hal_stats.stats[bp]['function'])

    # print method
    try:
        intercept, ret_value = method(cls, qemu, pc)
    except:
        log.exception("Error executing handler %s" % (repr(method)))
        # todo: alert control channels that
        # emulation is now in an inconsistent state, potentially.
        raise

    if intercept:

        abipkg = importlib.import_module("halucinator.arch.%s.abi")
        abipkg.function_return_transform(ret_value, qemu.regs)
        # qemu.exec_return(ret_value)

    qemu.cont()

# Traphandler handles trap messages from the avatar2 framework. These are 
# SigTrapHitMessage types and have two paramaters:
#  .address = where the trap happened.
#  .origin  = what object inside avatar2 this came from.
#             this is the qemu emulator.
# This function references bp2handler_addr_lut, which maps breakpoint numbers to 
# breakpoint handlers.
def traphandler(avatar, message):

    # TODO: this needs to be tidied up.

    qemu = message.origin
    archpkg = arch.arch_packagestring(qemu.architecture())

    if isinstance(qemu, ARMv7mQemuTarget):
        # TODO: THUMB bit make generic.
        pc = qemu.regs.pc & 0xFFFFFFFE  # Clear Thumb bit
    else:
        pc = qemu.regs.pc


    if len(bp2handler_lut.items()) == 0:

        # We have no interrupt handlers. 
        # The only thing we can do is continue the VM
        qemu.cont()
        return

    bp = bp2handler_addr2bp[message.address]
    log.info("SIGTRAP at address %x PC=%x Translated Num=%d" % (message.address, qemu.regs.pc, bp))
    log.info(bp2handler_addr2bp)

    try:
        cls, method = bp2handler_lut[bp]
    except KeyError:
        log.exception("Unable to find handler for %8x" % bp)
        qemu.cont()
        return


    
    hal_stats.stats[bp]['count'] += 1
    hal_stats.write_on_update(
        'used_intercepts', hal_stats.stats[bp]['function'])

    # print method
    try:
        intercept, ret_value = method(cls, qemu, pc)
    except:
        log.exception("Error executing handler %s" % (repr(method)))
        # todo: alert control channels that
        # emulation is now in an inconsistent state, potentially.
        raise

    explode = False

    if type(intercept) == list or type(intercept) == tuple:
        intercept, explode=intercept

    if intercept:

        log.info("Executing Return")
        abipkg = importlib.import_module("halucinator.arch.%s.abi" % archpkg)
        abipkg.function_return_transform(ret_value, qemu.regs, qemu, explode)
        #qemu.exec_return(ret_value)

    qemu.cont()

