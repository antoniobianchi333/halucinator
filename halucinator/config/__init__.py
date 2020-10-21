
import os
import yaml

from ..util.collections import *
from ..util.virtualenv import virtualenv_detect
from ..util.logging import *
from ..arch import Architecture

class Config(dict):
    """ 
    This class represents a configuration file in memory as a dictionary. 
    It knows how to load a config file from YAML and merge in "include" 
    files.
    """

    GLOBAL_ETC_PATH = "/etc/halucinator"
    GLOBAL_LIBRARY_PATH = "/etc/halucinator/library"
    GLOBAL_CONFIG_PATH = "/etc/halucinator/config.yaml"

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.venv_path = virtualenv_detect()

    def resolve_includes(self, resolver=None):

        """ this helper method will load a $path from

        VENV/etc/halucinator/library/$path
        or
        /etc/halucinator/library/$path
        if not in a virtualenv

        PATH is of the form:

            library:path/to/file

        otherwise this function does nothing.
        """
        def resolve_library_path(path):
            if not(path.startswith("library:")):
                return path
            
            library_path = path[8:]
            if self.venv_path != None:
                resolved_path = os.path.join(self.venv_path, 
                    self.GLOBAL_LIBRARY_PATH[1:])
            else:
                resolved_path = self.GLOBAL_LIBRARY_PATH
            resolved_path = os.path.join(resolved_path, library_path)
            return resolved_path

        includelist = list(nesteddictfilter(self, keyfilter=lambda k: k=="include"))

        # go through the include items
        for key,ivalue in includelist:

            # is it just one item?
            if type(ivalue)==str:
                self = Config(nesteddictupdate(self, 
                    key, 
                    Config.load_from_yaml_file(includefile, resolver)))

            # is it a list of items to include?
            elif type(ivalue)==list:

                # parse each one and merge them all:
                d = dict()
                for includefile in ivalue:

                    # special path, or just a file?
                    includefile = resolve_library_path(includefile)

                    # load the input dictionary.
                    inputdict = Config.load_from_yaml_file(includefile, resolver) 

                    # merge it into self:
                    for k,v in inputdict.items():
                        values = d.get(k, None)
                        if values != None:
                            if type(values) == dict and type(v) == dict:
                                # try to merge dictionaries:
                                d[k] = {**v, **values}
                            else:
                                if type(values) == type(v):
                                    # don't override local config.
                                    pass
                                else:
                                    raise RuntimeError("Config file parser can't resolve config import. Different types encountered that cannot be merged.")
                        else:
                            d[k] = v

                # Replace the include key with the input dictionary.
                self = Config(nesteddictupdate(self, 
                    key, 
                    d))
    
    def load_global_config(self):

        global_config_path=""
        if self.venv_path:
            global_config_path = os.path.join(self.venv_path, self.GLOBAL_CONFIG_PATH[1:])
        else:
            global_config_path = self.GLOBAL_CONFIG_PATH

        global_config = Config.load_from_yaml_file(global_config_path)
        for k,v in global_config.items():
            values = self.get(k, None)
            if values != None:
                if type(values) == dict and type(v) == dict:
                    # try to merge dictionaries:
                    self[k] = {**v, **values}
                else:
                    if type(values) == type(v):
                        # don't override local config.
                        pass
                    else:
                        raise RuntimeError("Config file parser can't resolve local/global config. Different types encountered.")
            else:
                self[k] = v

    @classmethod
    def load_from_yaml_file(cls, path, resolver=None):

        if resolver == None:
            with open(path, 'rb') as f:
                fullcontent = f.read()
        else:
            fullcontent = resolver(path)
        
        config = yaml.load(fullcontent, Loader=yaml.FullLoader)
    
        return cls(**config)

    @classmethod
    def load(cls, path, resolver=None):

        # load a config object from the path.
        config = Config.load_from_yaml_file(path, resolver)

        # resolve includes:
        config.resolve_includes(resolver)

        # check the file format does not contain invalid keywords.
        if "global" in config:
            raise ValueError("Config files may not contain a global object")

        # now load from the global config
        config.load_global_config()

        return config

    def dump(self):
        print(yaml.dump(dict(**self)))
    def dumps(self):
        return str(yaml.dump(dict(**self)))


# TODO: should these be where they are?


def qemu_find(config):

    # allow the location to be specified as an environment variable
    # this is to allow custom locations to be specified.
    qemu_env = os.environ.get("HALUCINATOR_QEMU")

    arch = config["ARCHDEF"]
    qemukey = ""

    # TODO: move this dependency into Arch, so that there is one point 
    # of failure.
    # or else define it somewhere else in here.
    if arch == Architecture.CORTEXM:
        qemukey = "arm_qemu_location"
    elif arch == Architecture.AVR8:
        qemukey = "avr_qemu_location"
    else:
        log.error("Unknown Architecture, unable to find qemu")
        return None

    qemu_config = config.get(qemukey, None)

    # Config rules are as follows: 
    # environment variable > global config > default
    qemu_location = None

    # if both config and env are set, env takes precedence
    # if only one is set, this will ensure that option is set to qemu_location.

    if qemu_config != None:
        qemu_location = qemu_config

    if qemu_env != None:
        qemu_location = qemu_env

    if qemu_location:
        if not os.path.exists(qemu_location):
            log.error("ERROR: Could not find qemu at %s did you build it?" % qemu_location)
        else:
            log.info("Found qemu in %s" % qemu_location)
    else:
        log.critical("Logic Error. Unable to find qemu.")
    return qemu_location

def get_memory_backing_file(memory, base_dir):
    '''
    Gets the filename for the memory to load into memory
    Args:
        memory(dict): Dict from yaml config file for memory 
                          requires keys [base_addr, size] 
                          optional keys [emulate (a memory emulator), 
                          perimissions, filename]
    Returns: 
        None - if there is no file backing this memory
        Path - the absolute path of the file to be loaded.
    '''

    filename = memory.get('file', None)
    if filename:
        if base_dir != None and not os.path.isabs(filename):
            filename = os.path.join(base_dir, filename)
    return filename

