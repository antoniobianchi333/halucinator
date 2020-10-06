import os
from ..util.logging import *

def gdb_find(config):
    # locate the distribution's GDB.
    
    gdb_location = None
    gdb_config = config.get("gdb_location", None)
    gdb_env = os.environ.get("HALUCINATOR_GDB")

    if gdb_config != None:
        gdb_location = gdb_config
    if gdb_env != None:
        gdb_location = gdb_config

    if not os.path.exists(gdb_location):
        log.error("Could not find gdb at %s did you build it?" % gdb_location)
    else:
        log.info(("Found qemu in %s" % gdb_location))
    return gdb_location

