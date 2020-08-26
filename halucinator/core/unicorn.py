

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
