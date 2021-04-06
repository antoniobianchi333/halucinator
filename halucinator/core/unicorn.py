"""
This is the Unicorn interface for Halucinator
"""

import unicorn
import archinfo
import types
from .handlers import add_block_hook
import struct
from collections import defaultdict
from .interactive import interactive_break as ibreak

# SparklyUnicorn: A syntactic wrapper for working with Unicorn's objects that does not make my head hurt

class UnicornRegisters(object):

    _uc = None

    def __init__(self, uc):
        self._uc = uc

    def __getattribute__(self, regname):
        for x in dir(unicorn.arm_const):
            if x.endswith('_' + regname.upper()):
                return self._uc.reg_read(getattr(unicorn.arm_const, x))
        return object.__getattribute__(self, regname)

    def get_all(self):
        out = {}
        self._uc = object.__getattribute__(self, '_uc')
        for reg in self._uc.arch.register_list:
            if not reg.artificial:
                n = reg.name
                try:
                    val = getattr(self, reg.name)
                    out[n] = val
                except AttributeError:
                    pass
        return out


    def __setattr__(self, regname, val):
        if regname == "_uc":
            object.__setattr__(self, regname, val)
        
        for x in dir(unicorn.arm_const):
            if x.endswith('_' + regname.upper()):
                return self._uc.reg_write(getattr(unicorn.arm_const, x), val)
        return object.__getattribute__(self, regname)

    def __repr__(self):
        s = "Unicorn Registers:\n----------------\n"
        for reg in self._uc.arch.register_list:
            if not reg.artificial:
                n = reg.name
                try:
                    val = getattr(self, reg.name)
                    s += "%s: %#08x\n" % (n, val)
                except AttributeError:
                    pass
        return s


class UnicornMemory(object):

    _uc = None

    def __init__(self, uc):
        self._uc = uc

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._uc.mem_read(key.start, (key.stop-key.start))
            # todo, striding support
        else:
            return self._uc.mem_read(key, 4)
            # TODO: Word size via archinfo

    def __setitem__(self, key, value):
        if isinstance(value, bytes):
            self._uc.mem_write(key, value)
        else:
            raise ValueError("Must be a bytes object")


class UnicornStack(object):

    _uc = None

    def __init__(self, uc):
        self._uc = uc

    def __getitem__(self, key):
        sp = self._uc.reg_read(unicorn.arm_const.UC_ARM_REG_SP)
        if isinstance(key, slice):
            return self._uc.mem_read(sp + key.start, (key.stop-key.start))
            # todo, striding support
        else:
            return self._uc.mem_read(sp + key, 4)
            # TODO: Word size via archinfo

    def __setitem__(self, key, value):
        if isinstance(value, bytes):
            self._uc.mem_write(sp + key, value)
        else:
            raise ValueError("Must be a bytes object")

    def _pp(self, start=-0x10, end=0x10, downward=True):
        if start % 4 != 0 or end % 4 != 0:
            print("WARNING: Dude, the stack on ARM is word-aligned! Did you skip ARM day?")
            start -= start % 4
            end -= end % 4
        data = self[start:end]
        sp = self._uc.regs.sp
        start_addr = sp+start
        end_addr = sp+end
        regs = self._uc.regs.get_all()

        points_to = defaultdict(list)
        for reg, val in regs.items():
            points_to[val - (val % 4)].append(reg)
        out = []
        for word in range(0, len(data), 4):
            bs = struct.unpack(">I", data[word:word+4])[0]
            line = "%#08x(SP%+#02x): %#010x" % (start_addr+word, (start_addr+word)-sp, bs)
            if points_to[start_addr+word]:
                line += "<-" + ",".join(points_to[start_addr+word])
            out.append(line)
        if downward is True:
            out = list(reversed(out))
        return "\n".join(out)

    def pp(self, start, end, downward=False):
        print(self._pp(start, end, downward))


class UnicornEmulator(object, UnicornRegisters, UnicornMemory, UnicornStack):

    def __init__(self, uc):
        self._uc = uc



    def step(self, fancy=False):
        curpc = self.reg_read(unicorn.arm_const.UC_ARM_REG_PC)
        result = self.emu_start(curpc | 1, 0, timeout=0, count=1)
        newpc = self.reg_read(unicorn.arm_const.UC_ARM_REG_PC)
        size = newpc - curpc
        if fancy:
            cs = self.arch.capstone
            mem = self.mem_read(curpc, 4) # TODO: FIXME
            insns = list(cs.disasm_lite(bytes(mem), size))
            for (cs_address, cs_size, cs_mnemonic, cs_opstr) in insns[:1]:
                print("    Instr: {:#08x}:\t{}\t{}".format(curpc, cs_mnemonic, cs_opstr))


def add_breakpoint(addr):
    global breakpoints
    breakpoints.append(addr)
    return breakpoints.index(addr)


def del_breakpoint(handle):
    global breakpoints
    if handle in breakpoints:
        breakpoints[breakpoitns.index(handle)] = -1
    else:
        breakpoints[handle] = -1


breakpoints = []
def breakpoint_handler(uc, address, size, user_data):
    global breakpoints
    if address in breakpoints:
        print("[*] Breakpoint hit at %#089x" % address)
        break_it(uc)


def unicorn_add_wrappers(uc, args):
    global breakpoints
    uc.regs = SparklyRegs(uc)
    uc.mem = SparklyMem(uc)
    uc.stack = SparklyStack(uc)
    uc.step = types.MethodType(step, uc)
    if args.debug and args.breakpoint:
        add_block_hook(breakpoint_handler)
        breakpoints.append(args.breakpoint)
    uc.arch = archinfo.ArchARMCortexM()
    return uc


def unicorn_configure(args):
    print("Loading configuration in %s" % args.config)
    with open(args.config, 'rb') as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)
    if 'include' in config:
        # Merge config files listed in 'include' in listed order
        # Root file gets priority
        newconfig = {}
        for f in config['include']:
            # Make configs relative to the including file
            if not f.startswith("/"):
                cur_dir = os.path.dirname(args.config)
                f = os.path.abspath(os.path.join(cur_dir, f))
            print("\tIncluding configuration from %s" % f)
            with open(f, 'rb') as infile:
                _merge_dict(newconfig, yaml.load(infile, Loader=yaml.FullLoader))
        _merge_dict(newconfig, config)
        config = newconfig

    # Step 2: Set up the memory map
    if 'memory_map' not in config:
        print("Memory Configuration must be in config file")
        quit(-1)


    # Create the unicorn
    # TODO: Parse the arch, using archinfo
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)

    regions = {}
    for rname, region in config['memory_map'].items():
        prot = 0
        if 'permissions' in region:
            prot = 7 # UC_PROT_ALL
        if 'r' in region['permissions']:
            prot |= 1
        if 'w' in region['permissions']:
            prot |= 2
        if 'x' in region['permissions']:
            prot |= 4
        print("Mapping region %s at %#08x, size %#08x, perms: %d" % (rname, region['base_addr'], region['size'], prot))
        regions[rname] = (region['base_addr'], region['size'], prot)
        uc.mem_map(region['base_addr'], region['size'], prot)
        if 'file' in region:
            file_offset = 0
            load_offset = 0
            file_size = region['size']
            if 'file_offset' in region:
                file_offset = region['file_offset']
            if 'load_offset' in region:
                load_offset = region['load_offset']
            if 'file_size' in region:
                file_size = region['file_size']
            if not region['file'].startswith("/"):
                cur_dir = os.path.dirname(args.config)
                f = os.path.join(cur_dir, region['file'])
            print("Using file %s, offset %#08x, load offset: %#08x, file_size: %#08x" % (f, file_offset, load_offset, file_size))
            with open(f, 'rb') as fp:
                fp.seek(file_offset)
                region_data = fp.read(file_size)
                print("Loading %#08x bytes at %#08x" % (len(region_data), region['base_addr'] + load_offset))
                uc.mem_write(region['base_addr'] + load_offset, region_data)
    globs.regions = regions

    # Native mmio fuzzing
    if not os.path.exists(args.native_lib):
        print("Native library %s does not exist!" % args.native_lib)
        exit(1)
    native.init(uc, args.native_lib, False, [], 0, None, [])

    name_to_addr = {}
    addr_to_name = {}

    # Create the symbol table
    if 'symbols' in config:
        addr_to_name = {k&0xFFFFFFFE: v for k, v in config['symbols'].items()}
        name_to_addr = {v: k for k, v in config['symbols'].items()}

    # Step 3: Set the handlers
    if 'handlers' in config and config['handlers']:
        for fname, handler_desc in config['handlers'].items():
            if 'addr' in handler_desc and isinstance(handler_desc['addr'], int):
                # This handler is always at a fixed address
                handler_desc['addr'] = handler_desc['addr'] & 0xFFFFFFFE  # Clear thumb bit
                addr_to_name[handler_desc['addr']] = fname
            else:
                # No static address specified, look in the symbol table
                if not name_to_addr:
                    print("Need symbol table in order to hook named functions!")
                    sys.exit(1)
                if fname not in name_to_addr:
                    # We can't hook this
                    print("No symbol found for %s" % fname)
                    continue
                handler_desc['addr'] = name_to_addr[fname]
            if not 'do_return' in handler_desc:
                handler_desc['do_return'] = True

            if 'handler' not in handler_desc:
                handler_desc['handler'] = None

            # Actually hook the thing
            print("Handling function %s at %#08x with %s" % (fname, handler_desc['addr'], handler_desc['handler']))
            add_func_hook(uc, handler_desc['addr'], handler_desc['handler'], do_return=handler_desc['do_return'])


    if args.ram_trace_file is not None:
        trace_mem.init_ram_tracing(uc, args.ram_trace_file, config)

    if args.bb_trace_file is not None:
        trace_bbs.register_handler(uc, args.bb_trace_file)

    if args.debug and args.trace_memory:
        add_block_hook(unicorn_debug_block)
        uc.hook_add(UC_HOOK_MEM_WRITE | UC_HOOK_MEM_READ, unicorn_debug_mem_access)

    if args.debug and args.trace_funcs:
        add_block_hook(unicorn_trace_syms)

    # This is our super nasty crash detector
    uc.hook_add(UC_HOOK_MEM_WRITE_UNMAPPED | UC_HOOK_MEM_READ_INVALID, unicorn_debug_mem_invalid_access)

    # Set the program entry point
    # TODO: Make this arch-independent
    if not 'entry_point' in config:
        print("Binary entry point missing! Make sure 'entry_point is in your configuration")
        sys.exit(1)
    # Set the initial stack pointer
    # TODO: make this arch-independent
    uc.reg_write(UC_ARM_REG_PC, config['entry_point'])
    uc.reg_write(UC_ARM_REG_SP, config['initial_sp'])


    # Implementation detail: Interrupt triggers need to be configured before the nvic (to enable multiple interrupt enabling)
    if 'interrupt_triggers' in config:
        interrupt_triggers.init_triggers(uc, config['interrupt_triggers'])

    use_nvic = ('use_nvic' in config and config['use_nvic'] is True)
    if use_nvic:
        vtor = globs.NVIC_VTOR_NONE
        num_vecs = globs.DEFAULT_NUM_NVIC_VECS
        if 'nvic' in config:
            num_vecs = config['nvic']['num_vecs'] if 'num_vecs' in config['nvic'] else globs.DEFAULT_NUM_NVIC_VECS

        native.init_nvic(uc, vtor, num_vecs, False)

    # Configure abstract peripheral models
    configure_models(uc, config)

    # At the end register the non-native accumulating block hook if any unconditional hooks have been registered
    if handlers.func_hooks:
        # In the native version we use a native check wrapper to avoid unconditional python block hooks
        native.register_cond_py_handler_hook(uc, handlers.func_hooks.keys())
    else:
        print("No function hooks found. Registering no native basic block hook for that")

    uc.symbols = name_to_addr
    uc.syms_by_addr = addr_to_name
    uc = add_sparkles(uc, args)
    register_global_block_hook(uc)
    return uc
