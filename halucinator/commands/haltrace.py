
import os
import sys
import yaml
import re
import fileinput

def main():
    '''
    Gets Symbols from elf file using the symbols table in the elf
    '''
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-a', '--addressfile', required=True,
                   help='HALucinator Address Symbols File')
    p.add_argument('-o', '--out', required=True,
                   help='Output File to save trace')

    args = p.parse_args()

    outfile = args.out
    addressf = args.addressfile

    print("HAL-Trace Control Flow Analysis Tool")
    print("Reading Trace from stdin")
    print("Using Address File %s" % addressf)
    print("Using Output File %s" % outfile)

    with open(addressf, 'rb') as f:
        adrf = yaml.load(f, Loader=yaml.FullLoader)
    

    symdict = adrf.get("symbols", None)

    if symdict == None:
        print("Unable to find symbol table in the address file")
        quit(-1)

    hexline = re.compile(r'^0x')

    with open(outfile, 'wb+') as log:
        try:
            for line in fileinput.input(files=()):
                if not hexline.match(line):
                    continue

                seppos = line.find(":")
                pcstr = line[0:seppos]
                pc = int(pcstr, 16)

                symbol = symdict.get(pc, '')

                outp = "0x%08x - %s" % (pc, symbol)
                print(outp)
                outp += "\n"
                log.write(outp.encode("utf-8"))
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()    




