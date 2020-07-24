
import os
from . import hal_stats

PATCH_MEMORY_SIZE = 4096
INTERCEPT_RETURN_INSTR_ADDR = 0x20000000 - PATCH_MEMORY_SIZE

def get_memory_filename(memory, base_dir):
    '''
    Gets the filename for the memory to load into memory
    Args:
        memory(dict): Dict from yaml config file for memory 
                          requires keys [base_addr, size] 
                          optional keys [emulate (a memory emulator), 
                          perimissions, filename]

    '''
    filename = memory['file'] if 'file' in memory else None
    if filename != None:
        if base_dir != None and not os.path.isabs(filename):
            filename = os.path.join(base_dir, filename)
    return filename

def add_patch_memory(avatar, qemu):
    ''' 
        Use a patch memory to return from intercepted functions, as 
        it allows tracking number of intercepts
    '''

    log.info("Adding Patch Memory %s:%i" %
             (hex(INTERCEPT_RETURN_INSTR_ADDR), PATCH_MEMORY_SIZE))
    avatar.add_memory_range(INTERCEPT_RETURN_INSTR_ADDR, PATCH_MEMORY_SIZE,
                            name='patch_memory', permissions='rwx')


def write_patch_memory(qemu):
    BXLR_ADDR = INTERCEPT_RETURN_INSTR_ADDR | 1
    CALL_RETURN_ZERO_ADDR = BXLR_ADDR + 2
    BXLR = 0x4770
    BXR0 = 0x4700
    BLXR0 = 0x4780
    MOVS_R0_0 = 0x0020
    POP_PC = 0x00BD

    qemu.write_memory(INTERCEPT_RETURN_INSTR_ADDR, 2, BXLR, 1)

    # Sets R0 to 0, then return to address on stack
    qemu.write_memory(CALL_RETURN_ZERO_ADDR, 2, MOVS_R0_0, 1)
    qemu.write_memory(CALL_RETURN_ZERO_ADDR+2, 2, POP_PC, 1)

    def exec_return(value=None):
        if value is not None:
            qemu.regs.r0 = value
        qemu.regs.pc = BXLR_ADDR
    qemu.exec_return = exec_return

    def write_bx_lr(addr):
        qemu.write_memory(addr, 2, BXLR, 1)
    qemu.write_bx_lr = write_bx_lr

    def write_bx_r0(addr):
        qemu.write_memory(addr, 2, BXR0, 1)
    qemu.write_bx_r0 = write_bx_r0

    def write_blx_r0(addr):
        qemu.write_memory(addr, 2, BLXR0, 1)
    qemu.write_blx_r0 = write_blx_r0

    def call_ret_0(callee, arg0):
        # Save LR
        sp = qemu.regs.sp - 4
        qemu.regs.sp = sp
        qemu.write_memory(sp, 4, qemu.regs.lr, 1)
        # Set return to out patch that will set R0 to 0
        qemu.regs.lr = CALL_RETURN_ZERO_ADDR
        qemu.regs.r0 = arg0
        qemu.regs.pc = callee
    qemu.call_ret_0 = call_ret_0

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

    filename = get_memory_filename(memory, base_dir)

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



