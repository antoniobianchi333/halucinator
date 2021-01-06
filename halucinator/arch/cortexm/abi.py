#!/usr/bin/env python

def function_return_transform(value, regs):

    if value != None:
        regs.r0 = value
    else:
        regs.r0 = 0
    regs.pc = regs.lr
    return
