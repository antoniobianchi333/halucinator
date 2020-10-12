

from ..util.logging import *
import sys

def python_version_check():

    major, minor = sys.version_info.major, sys.version_info.minor

    if major < 3 or (major == 3 and minor <= 5):
        log.critical("Python version 3.5 or later required, version %d.%d detected" % (major, minor))
        return False

    return True

class HalucinatorRehost(object):

    def __init__(self):
        pass

