#!/usr/bin/env python

import os
import logging
from importlib import __import__ as pyimport
from argparse import ArgumentParser, REMAINDER



log = logging.getLogger("Halucinator-Peripheral")
log.setLevel(logging.DEBUG)

"""
This function is the entrypoint for the halucinator-periph command. 
This command finds and loads a package, expecting it to implement 
the peripheral server interface 
"""
def main():

    p = ArgumentParser()
    p.add_argument('-m', '--module', dest='module', type=str, required=True,
                   help='Module to be invoked as a peripheral server')
    p.add_argument('remainder', nargs=REMAINDER)

    args = vars(p.parse_args())

    print(args)
    module = None
    modulename = args.get("module", "")
    if modulename != "":
        try:
            module = pyimport(modulename)
        except ModuleNotFoundError:
            log.critical("Module %s is unknown to python. If it is found in a virtualenv, install halucinator there." % modulename)
            exit(1)
    else:
        log.critical("Module not supplied.")
        exit(1)

    print(module)
    print(module.getattrs())
