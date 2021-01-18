# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.

from os import sys, path
from ...peripheral_models.rs232 import SerialPublisher
from ..bp_handler import BPHandler, bp_handler
import logging
log = logging.getLogger("AVR8IVT")
log.setLevel(logging.DEBUG)

class AVR8IVT(BPHandler):

    def __init__(self, impl=None):
        pass

    @bp_handler(['__RESET'])
    def handle_reset(self, qemu, bp_addr):
        log.info("RESET VECTOR FUNCTION EXECUTED")

        return False, 0



