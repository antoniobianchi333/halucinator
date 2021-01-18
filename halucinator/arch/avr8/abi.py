#!/usr/bin/env python

def function_return_transform(value, regs, emulator=None):

    if value != None:
        MSB = (value & 0xFF00) >> 8
        LSB = value & 0x00FF

        regs.r24 = LSB
        regs.r25 = MSB

    else:
        regs.r24 = 0
        regs.r25 = 0

    # The AVR architecture stores return addresses in the IO Stack, pointed to 
    # by the SP pseudo-register. Fetch it, and set the program counter.
    retpointer = emulator.read_memory(regs.SP, 1, 16, False)
    print(retpointer)
    retpointer = emulator.read_memory(regs.SP, 1, 1, False)
    regs.pc = int(retpointer)


    
