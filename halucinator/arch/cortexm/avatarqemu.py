# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from avatar2 import Avatar, QemuTarget
from avatar2.archs.architecture import *
from avatar2.archs import arm as avatararch
from halucinator.util.logging import *

PATCH_MEMORY_SIZE = 4096
INTERCEPT_RETURN_INSTR_ADDR = 0x20000000 - PATCH_MEMORY_SIZE

class ARMQemuTarget(QemuTarget):
    '''
        Implements a QEMU target that has function args for use with
        halucinator.  Enables read/writing and returning from
        functions in a calling convention aware manner
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_sp = 0

    def get_arg(self, idx):
        '''
            Gets the value for a function argument (zero indexed)

            :param idx  The argument index to return
            :returns    Argument value
        '''
        if idx >= 0 and idx < 4:
            return self.read_register("r%i" % idx)
        elif idx >= 4:
            sp = self.read_register("sp")
            stack_addr = sp + (idx-4) * 4
            return self.read_memory(stack_addr, 4, 1)
        else:
            raise ValueError("Invalid arg index")

    def set_arg(self, idx, value):
        '''
            Sets the value for a function argument (zero indexed)


            :param idx      The argument index to return
            :param value    Value to set index to 
        '''
        if idx >= 0 and idx < 4:
            self.write_register("r%i" % idx, value)
        elif idx >= 4:
            sp = self.read_register("sp")
            stack_addr = sp + (idx-4) * 4
            self.write_memory(stack_addr, 4, value)
        else:
            raise ValueError(idx)

    def get_ret_addr(self):
        '''
            Gets the return address for the function call

            :returns Return address of the function call
        '''
        return self.regs.lr

    def set_ret_addr(self, ret_addr):
        '''
            Sets the return address for the function call
            :param ret_addr Value for return address
        '''
        self.regs.lr = ret_addr

    def execute_return(self, ret_value):
        if ret_value != None:
            # Puts ret value in r0
            self.regs.r0 = ret_value
        self.regs.pc = self.regs.lr


    def irq_set(self, irq_num=1, cpu=0):
        self.protocols.monitor.execute_command("avatar-set-irq", 
            args={"cpu_num":cpu, "irq_num": irq_num, "value":1})

    def irq_clear(self, irq_num=1, cpu=0):
        self.protocols.monitor.execute_command("avatar-set-irq", 
            args={"cpu_num":cpu, "irq_num": irq_num, "value":0})

    def irq_pulse(self, irq_num=1, cpu=0):
        self.protocols.monitor.execute_command("avatar-set-irq", 
            args={"cpu_num":cpu, "irq_num": irq_num, "value":3})


    def get_symbol_name(self, addr):
        """
        Get the symbol for an address

        :param addr:    The name of a symbol whose address is wanted
        :returns:         (Symbol name on success else None
        """

        return self.avatar.config.get_symbol_name(addr)


class ARMv7mQemuTarget(ARMQemuTarget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def trigger_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-inject-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})

    def set_vector_table_base(self, base, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-set-vector-table-base',
            {'base': base, 'num_cpu': cpu_number})

    def enable_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-enable-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})


    def trigger_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-inject-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})


    def set_vector_table_base(self, base, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-set-vector-table-base',
            {'base': base, 'num_cpu': cpu_number})


    def enable_interrupt(self, interrupt_number, cpu_number=0):
        self.protocols.monitor.execute_command(
            'avatar-armv7m-enable-irq',
            {'num_irq': interrupt_number, 'num_cpu': cpu_number})


def add_patch_memory(avatar):
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

    """
    These instructions are as follows:

       47 70      	bx	 lr
       47 00      	bx	 r0
       47 80      	blx	 r0
       00 20      	movs r0, #0
       00 bd     	pop	{pc}
    """
    
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

def arch_specific_setup(config, qemu):
    # TODO: fix this in upstream
    # Work around Avatar-QEMU's improper init of Cortex-M3
    qemu.regs.cpsr |= 0x20  # Make sure the thumb bit is set
    qemu.regs.sp = qemu.init_sp  # Set SP as Qemu doesn't init correctly
    
    
    nvic_base = int(config.get("nvic_base", 0x08000000))

    qemu.set_vector_table_base(nvic_base)


def resolve_avatar_cpu(config):
    # TODO: Select M0, M0+, M4, M7 etc as appropriate.
    return avatararch.ARM_CORTEX_M3

emulator = ARMv7mQemuTarget
