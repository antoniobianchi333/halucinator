
import os
import yaml

class Config(dict):
    """ 
    This class represents a configuration file in memory as a dictionary.
    
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    """def merge_shallow(self, other):
        if not isinstance(other, Config):
            raise ValueError("Can't merge other of type %s" % type(other))
        newdict = {**self, **other}
        self.update(newdict)"""


    def resolve_includes(self, srcfile, resolver=None):

        include_items = self.get("include")
        if include_items != None:
            for include in include_items:
                if not include.startswith("/"):
                    cur_dir = os.path.dirname(args.config)
                    include = os.path.abspath(os.path.join(cur_dir, include))
                
                replaceconfig = resolver(include)
                
                if replaceconfig != None:
                    pass
                else:
                    raise IOError("Something failed reading/decoding %s" % include)
        
    @classmethod
    def load_from_yaml_file(cls, filepath):
        with open(args.config, 'rb') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        return cls(**config)

def gdb_find(config):
    # locate the distribution's GDB.
    
    hostconfig = config["host"]
    gdb_config = hostconfig.get("gdb_location", None)
    gdb_env = os.environ.get("HALUCINATOR_QEMU")

    if gdb_config != None:
        gdb_location = gdb_config
    if gdb_env != None:
        gdb_location = gdb_config

    if not os.path.exists(gdb_location):
        print(("ERROR: Could not find gdb at %s did you build it?" % gdb_location))
        exit(1)
    else:
        print(("Found qemu in %s" % qemu_location))
    return qemu_location

def qemu_find(config):

    # NOTE: using golang's "naming" conventions here to put all 
    # dependencies in vendor, as git submodules to allow managing 
    # versions more nicely than scripts.
    # this is assumed to be executed from the root of the repository
    qemu_location_default = "vendor/avatar2/targets/build/qemu/arm-softmmu/qemu-system-arm"

    # allow the location to be specified as an environment variable
    # this is to allow custom locations to be specified.
    qemu_env = os.environ.get("HALUCINATOR_QEMU")
    
    hostconfig = config["host"]
    qemu_config = hostconfig.get("qemu_location", None)

    # Config rules are as follows: 
    # environment variable > global config > default
    
    if qemu_env == None or qemu_config == None:
        qemu_location = qemu_location_default
    else:
        # if both config and env are set, env takes precedence
        # if only one is set, this will ensure that option is set to qemu_location.

        if qemu_config != None:
            qemu_location = qemu_config

        if qemu_env != None:
            qemu_location = qemu_env
    
    if not os.path.exists(qemu_location):
        print(("ERROR: Could not find qemu at %s did you build it?" % qemu_location))
        exit(1)
    else:
        print(("Found qemu in %s" % qemu_location))
    return qemu_location
