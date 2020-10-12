
from . import Architecture
from . import cortexm as cortexm
from . import avr8 as avr8

AVATARQEMULUT = {
    Architecture.CORTEXM: cortexm,
    Architecture.AVR8:    avr8,
}
