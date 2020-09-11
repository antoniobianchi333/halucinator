

def dwarfparse():
    # parse the command-line arguments and invoke ReadElf
    argparser = argparse.ArgumentParser(
        usage='usage: %(prog)s [options] <elf-file>',
        description="Parses DWARF debugging from elf file",
        prog='readelf.py')
    argparser.add_argument('file',
                           nargs='?', default=None,
                           help='ELF file to parse',)

    args = argparser.parse_args()

    if not args.file:
        argparser.print_help()
        sys.exit(0)

    with open(args.file, 'rb') as file:
        try:
            print("Running")
            reader = DWARFReader(file)
            print(reader.get_function_prototype('ETH_DMAReceptionEnable'))
            decl, size = reader.get_typedef_desc_from_die(
                'ETH_DMARxFrameInfos')
            print(decl, "Size: ", size)
        except ELFError as ex:
            sys.stderr.write('ELF error: %s\n' % ex)
            sys.exit(1)

if __name__ == '__main__':
    '''
    Gets Symbols from elf file using the symbols table in the elf
    '''
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-b', '--bin', required=True,
                   help='Elf file to get symbols from')
    p.add_argument('-o', '--out', required=False,
                   help='YAML file to save output to' +
                   'if will be output to (--bin).yaml')

    args = p.parse_args()
    if args.out == None:
        args.out = os.path.splitext(args.bin)[0] + "_addrs.yaml"

    functions = get_functions_and_addresses(args.bin)
    with open(args.out, 'w') as outfile:
        out_dict = format_output(functions)
        yaml.safe_dump(out_dict, outfile)






