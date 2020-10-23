# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from struct import unpack

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

    with open(binary_filename, 'rb') as bin_file:
        # https://docs.python.org/3/library/struct.html#format-characters
        entry = unpack('<H', bin_file.read(2))[0]

    return sp, entry