#!/usr/bin/env python3

import ctypes
import os

def load_library(libname):
    return ctypes.util.find_library(libname)
