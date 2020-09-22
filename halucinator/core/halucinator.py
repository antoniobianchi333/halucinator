

import logging
import sys


log = logging.getLogger("Halucinator")
log.setLevel(logging.DEBUG)
avalog = logging.getLogger("avatar")
avalog.setLevel(logging.WARN)
pslog = logging.getLogger("PeripheralServer")
pslog.setLevel(logging.WARN)
# log.setLevel(logging.DEBUG)


QemuTarget.trigger_interrupt = trigger_interrupt
QemuTarget.set_vector_table_base = set_vector_table_base
# --------------------------END QemuTarget Hack --------------------------------


def python_version_check():

    major, minor = sys.version_info.major, sys.version_info.minor

    if major < 3 or (major == 3 and minor <= 5):
        logging.critical("Python version 3.5 or later required, version %d.%d detected" % (major, minor))
        return False

    return True

class HalucinatorRehost(object):

	def __init__(self):
		pass

    