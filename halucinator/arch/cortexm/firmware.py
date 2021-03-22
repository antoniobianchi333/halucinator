# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from struct import unpack



class FirmwareImage(object):

    def __init__(self, filename='', *args, **kwargs):
        self.filename = filename

    def _entry_sp(self):
        with open(binary_filename, 'rb') as bin_file:
            sp, entry = unpack('<II', bin_file.read(8))

        self.stack_pointer = sp
        self.entry = entry

    def entrypoint(self):
        if self.entry == None:
            self._entry_sp()

        return self.entry

    def stackpointer(self):
        if self.stack_pointer == None:
            self._entry_sp()

        return self.stack_pointer



def get_sp_and_entry(binary_filename):
    '''
    Gets the initial stack pointer and entry point from the filename
    It assumes the passed file is loaded/aliased to address 0x00000000
    Args: 
        binary_filename(string):   path to file to open, assumes binary format

    Returns:
        sp(int), entry(int):  Stack pointer and entry point of board
    '''
    with open(binary_filename, 'rb') as bin_file:
        sp, entry = unpack('<II', bin_file.read(8))

    return sp, entry
