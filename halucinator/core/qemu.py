
import os

from avatar2 import Avatar, QemuTarget, ARM_CORTEX_M3, TargetStates
from avatar2.peripherals.avatar_peripheral import AvatarPeripheral

def find_qemu():

    # NOTE: using golang's "naming" conventions here to put all 
    # dependencies in vendor, as git submodules to allow managing 
    # versions more nicely than scripts.
    # this is assumed to be executed from the root of the repository
    # BUT a TODO further down should provide a configuration file variable 
    # for this.
    qemu_location_default = "vendor/avatar2/targets/build/qemu/arm-softmmu/qemu-system-arm"

    # allow the location to be specified as an environment variable
    # this is to allow custom locations to be specified.
    qemu_location = os.environ.get("HALUCINATOR_QEMU")
    if qemu_location == None:
        qemu_location = qemu_location_default

    # TODO: also allow config file usage.
    # TODO: switch to logger.
    if not os.path.exists(qemu_location):
        print(("ERROR: Could not find qemu in %s did you build it?" % qemu_location))
        exit(1)
    else:
        print(("Found qemu in %s" % qemu_location))
    return qemu_location

def get_qemu_target(name, entry_addr, firmware=None, log_basic_blocks=False,
                    output_base_dir='', gdb_port=1234):
    qemu_path = find_qemu()
    outdir = os.path.join(output_base_dir, 'tmp', name)
    hal_stats.set_filename(outdir+"/stats.yaml")
    avatar = Avatar(arch=ARM_CORTEX_M3, output_directory=outdir)
    print(("GDB_PORT", gdb_port))
    log.critical("Using qemu in %s" % qemu_path)
    qemu = avatar.add_target(QemuTarget,
                             gdb_executable="gdb-multiarch",
                             gdb_port=gdb_port,
                             qmp_port=gdb_port+1,
                             firmware=firmware,
                             executable=qemu_path,
                             entry_address=entry_addr, name=name)
    # qemu.log.setLevel(logging.DEBUG)

    if log_basic_blocks == 'irq':
        qemu.additional_args = ['-d', 'in_asm,exec,int,cpu,guest_errors,avatar,trace:nvic*', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    elif log_basic_blocks:
        qemu.additional_args = ['-d', 'in_asm', '-D',
                                os.path.join(outdir, 'qemu_asm.log')]
    return avatar, qemu

#  Add Interrupt support to QemuTarget, will eventually be in Avatar
#  So until then just hack in a patch like this
def trigger_interrupt(qemu, interrupt_number, cpu_number=0):
    qemu.protocols.monitor.execute_command(
        'avatar-armv7m-inject-irq',
        {'num_irq': interrupt_number, 'num_cpu': cpu_number})


def set_vector_table_base(qemu, base, cpu_number=0):
    qemu.protocols.monitor.execute_command(
        'avatar-armv7m-set-vector-table-base',
        {'base': base, 'num_cpu': cpu_number})


def enable_interrupt(qemu, interrupt_number, cpu_number=0):
    qemu.protocols.monitor.execute_command(
        'avatar-armv7m-enable-irq',
        {'num_irq': interrupt_number, 'num_cpu': cpu_number})
