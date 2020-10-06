#!/usr/bin/env python

import unittest
from halucinator.arch import *


class TestArchRecognizer(unittest.TestCase):

    def testArchitectureRecognition(self):

        arch, props = arch_find('Cortex-M0+')
        self.assertEqual(arch, Architecture.CORTEXM)
        arch, props = arch_find('Cortex-M0')
        self.assertEqual(arch, Architecture.CORTEXM)
        arch, props = arch_find('Cortex-M3')
        self.assertEqual(arch, Architecture.CORTEXM)
        arch, props = arch_find('Cortex-M4')
        self.assertEqual(arch, Architecture.CORTEXM)
        arch, props = arch_find('cortex-m4')
        self.assertEqual(arch, Architecture.CORTEXM)
        arch, props = arch_find('cortexm')
        self.assertEqual(arch, Architecture.CORTEXM)

        arch, props = arch_find('ARM cortexm')
        self.assertEqual(arch, Architecture.CORTEXM)


        arch, props = arch_find('avr')
        self.assertEqual(arch, Architecture.AVR8)
        arch, props = arch_find('ATmega328P')
        self.assertEqual(arch, Architecture.AVR8)
        arch, props = arch_find('atmega2560')
        self.assertEqual(arch, Architecture.AVR8)

        arch, props = arch_find('Alpha')
        self.assertEqual(arch, Architecture.UNKNOWN)
        arch, props = arch_find('MIPS')
        self.assertEqual(arch, Architecture.UNKNOWN)
