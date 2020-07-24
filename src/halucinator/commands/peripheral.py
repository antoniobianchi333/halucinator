#!/usr/bin/env python

import os
import logging
from argparse import ArgumentParser

log = logging.getLogger("Halucinator")
log.setLevel(logging.DEBUG)
avalog = logging.getLogger("avatar")
avalog.setLevel(logging.WARN)
pslog = logging.getLogger("PeripheralServer")
pslog.setLevel(logging.WARN)

"""
This function is the entrypoint for the halucinator-periph command. 
This command finds and loads a package, expecting it to implement 
the peripheral server interface 
"""
def main():
	pass