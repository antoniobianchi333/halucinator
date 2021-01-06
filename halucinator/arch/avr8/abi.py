#!/usr/bin/env python

def function_return_transform(value, regs):

    if value == None:
        MSB = (value & 0xFF00) >> 8
        LSB = value & 0x00FF

        regs.r24 = LSB
        regs.r25 = MSB


