#!/usr/bin/env python

import logging
log = logging.getLogger("AVR8SERIAL")
log.setLevel(logging.DEBUG)


def function_return_transform(value, regs, emulator=None, explode=False):

    if value != None:
        MSB = (value & 0xFF00) >> 8
        LSB = value & 0x00FF

        regs.r24 = LSB
        regs.r25 = MSB

    else:
        regs.r24 = 0
        regs.r25 = 0


    stackptr = regs.SP
    log.warn("RET: Return Stack Pointer %x" % int(stackptr))

    # The AVR architecture stores return addresses in the IO Stack, pointed to 
    # by the SP pseudo-register. Fetch it, and set the program counter.
    retpointer_high = emulator.read_memory(stackptr, 1, 1, False)
    retpointer_med = emulator.read_memory(stackptr+1, 1, 1, False)
    retpointer_low = emulator.read_memory(stackptr+2, 1, 1, False)

    stack = emulator.read_memory(stackptr, 1, 18, False)
    log.warn("RET: Stack looks like", stack)

    regs.SP = regs.SP + 2
    log.warn("RET: Return Stack Pointer %x" % int(emulator.regs.SP))

    retpointer = (retpointer_low | retpointer_med << 8 | retpointer_high << 16 ) *2
    log.warn("RET value set to 0x%x" % value)
    log.warn("RET PC = 0x%x" % int(retpointer))
    regs.pc = int(retpointer)

    if explode == True:
        raise Exception("Exploding as requested")
