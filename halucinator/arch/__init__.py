#!/usr/bin/env python

from enum import Enum
import re

# TODO: This roughly mirrors the work of angr's archinfo to detect architecture 
# from a given configuration name. 

architecture_list = []

class Architecture(Enum):
    UNKNOWN = 0
    CORTEXM = 1
    AVR8    = 2


def arch_register(regex, architecture, properties):
    architecture_list.append([regex, architecture, properties])

def arch_find(archstr):
    for regex, enum, props in architecture_list:
        if re.match(regex, archstr.lower()):
            return enum, props

    return Architecture.UNKNOWN, None

arch_register(r'.*cortexm|.*cortex\-m.*|.*v7\-m.*', 
              Architecture.CORTEXM, dict())
arch_register(r'avr.*|atmega.*',
              Architecture.AVR8, dict())

