
import logging
log = logging.getLogger("AVR8SERIAL")
log.setLevel(logging.DEBUG)

def function_return_transform(value, regs, emulator=None):

    if value != None:
        regs.r0 = value
    else:
        regs.r0 = 0
    regs.pc = regs.lr
    return


