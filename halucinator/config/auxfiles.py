

def get_memory_filename(memory, base_dir):
    '''
    Gets the filename for the memory to load into memory
    Args:
        memory(dict): Dict from yaml config file for memory 
                          requires keys [base_addr, size] 
                          optional keys [emulate (a memory emulator), 
                          perimissions, filename]

    '''
    filename = memory['file'] if 'file' in memory else None
    if filename != None:
        if base_dir != None and not os.path.isabs(filename):
            filename = os.path.join(base_dir, filename)
    return filename