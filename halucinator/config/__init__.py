
import os
import yaml

class Config(dict):
    """ 
    This class represents a configuration file in memory as a dictionary. 
    It knows how to load a config file from YAML and merge in "include" 
    files.
    """

    GLOBAL_ETC_PATH = "/etc/halucinator"
    GLOBAL_LIBRARY_PATH = "/etc/halucinator/library"
    GLOBAL_CONFIG_PATH = "/etc/halucinator/config.yml"

    def __init__(self, *args, **kwargs):

        self.venv_path = os.environ.get("VIRTUAL_ENV")
        self.update(*args, **kwargs)

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
                    self.GLOBAL_LIBRARY_PATH)
            else:
                resolved_path = self.GLOBAL_LIBRARY_PATH
            resolved_path = os.path.join(resolved_path, library_path)
            return resolved_path

        includelist = list(nesteddictfilter(d, keyfilter=lambda k: k=="include"))

        def include_load(iv):
        # files beginning with "library:"
            includefile = resolve_library_path(iv)

            return nesteddictupdate(self, 
                k, 
                Config.load_from_yaml_file(includefile, resolver))

        for key,ivalue in listofitems:
            if type(ivalue)==str:
                self = include_load(ivalue)
            elif type(ivalue)==list:
                for includefile in ivalue:
                    self = include_load(includefile)
    
    def load_global_config(self):

        if self.venv_path != None:
            global_config_path = os.path.join(self.GLOBAL_CONFIG_PATH, 
                self.venv_path)
        else:
            global_config_path = self.GLOBAL_CONFIG_PATH

        global_config = Config.load_from_yaml_file(global_config_path)
        self["global"] = global_config

    @classmethod
    def load_from_yaml_file(cls, filepath, resolver=None):

        if resolver == None:
            with open(args.config, 'rb') as f:
                fullcontent = f.read()
        else:
            fullcontent = resolver(filepath)
        
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

def gdb_find(config):
    # locate the distribution's GDB.
    
    hostconfig = config["global"]
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
    
    hostconfig = config["global"]
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
