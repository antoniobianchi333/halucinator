

import os
import sys
from halucinator.binfmt.elf import *

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


def main():
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
    p.add_argument('-t', '--text-relative', action='store_true', dest='textrelative', required=False,
                   help='Return offsets relative to the start of the text section if this will be treated as a binary, rather than ELF, under emulation')

    args = p.parse_args()
    if args.out == None:
        args.out = os.path.splitext(args.bin)[0] + "_addrs.yaml"

    
    elffile = ELFParser(args.bin)
    print("[*] Parsing ELF File: %s" % args.bin)
    print("[*] Writing output to: %s" % args.out)
    architecture = elffile.get_arch()
    functions = elffile.get_functions_and_addresses(args.textrelative)
    print("[*] Arch is: %s" % architecture)
    if args.textrelative:
        print("[*] Reporting symbols relative to base of text section. To report symbols relative")
        print("    to the file base, do not pass -t/--text-relative.")


    with open(args.out, 'w') as outfile:
        out_dict = format_output(functions, architecture=architecture)
        yaml.safe_dump(out_dict, outfile)

    print("[+] Output written to %s" % (outfile.name))

if __name__ == '__main__':
    main()    




