#!/usr/bin/env python3

import ctypes
from .os import load_library

def libcxx_find():
    names=["stdc++", "c++"]
    for name in names:
        library = load_library(name)
        if library is not None:
            return library
    return None

def libc_find():
    names=["c"]
    for name in names:
        library = load_library(name)
        if library is not None:
            return library
    return None


class InvalidName(Exception):
    pass

def demangle(name, libc, libcxx):

    mangled_name = ctypes.c_char_p(mangled.encode("utf-8"))
    status = ctypes.c_int()
    """
    char* abi::__cxa_demangle 	( 	const char *  	mangled_name,
		char *  	output_buffer,
		size_t *  	length,
		int *  	status	 
	) 	
    """
    retval = libcxx.__cxa_demangle(
        mangled_name,
        None,
        None,
        ctypes.pointer(status))
    
    try:
        demangled_name = retval.value
    finally:
        libc.free(retval)

    if status.value != 0:

        if status.value == -2:
            raise InvalidName(name)
        else:
            raise Exception("Error code: %d", status.value)
    
    return demangled_name.decode("utf-8")
