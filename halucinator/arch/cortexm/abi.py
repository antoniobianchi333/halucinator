
import logging
log = logging.getLogger("AVR8SERIAL")
log.setLevel(logging.DEBUG)

def function_return_transform(value, regs, emulator=None):

    if value != None:
        regs.r0 = value
    # if we have a None type: let us not touch r0, we don't know if 
    # the ABI will set r0 to 0 or not (even if it is a scratch/return 
    # register)
    #else:
    #    regs.r0 = 0
    regs.pc = regs.lr
    return


