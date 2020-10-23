# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from struct import unpack
from elftools.elf.elffile import ELFFile

def get_sp_and_entry(binary_filename):
    '''
    Gets the initial stack pointer and entry point from the filename
    It assumes the passed file is loaded/aliased to address 0x00000000
    Args: 
        binary_filename(string):   path to file to open, assumes binary format

    Returns:
        sp(int), entry(int):  Stack pointer and entry point of board
    '''
    # TODO: this is hardcoded for the UNO. We need to fix it.
    sp = 0x900
    entry = 0

    with open(binary_filename, 'rb+') as f:
        e = ELFFile(f)
        entry = e.header.e_entry
        print(entry)

    return sp, entry