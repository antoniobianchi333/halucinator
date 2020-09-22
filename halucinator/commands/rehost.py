#!/usr/bin/env python

import os
import logging
from argparse import ArgumentParser

import halucinator.config as cfg
import halucinator.core.avatarqemu as avatar


log = logging.getLogger("Halucinator")
log.setLevel(logging.DEBUG)
avalog = logging.getLogger("avatar")
avalog.setLevel(logging.WARN)
pslog = logging.getLogger("PeripheralServer")
pslog.setLevel(logging.WARN)

"""
This function is the entrypoint for the halucinator-rehost command. This is the entry point for 
emulating a binary.
"""
def main():
    
    p = ArgumentParser()
    p.add_argument('-c', '--config', required=True,
                   help='Configuration file used to run emulation')
    p.add_argument('-m', '--memory_config', required=False, default=None,
                   help='Memory Config, will overwrite config in --config if present if memories not in -c this is required')
    p.add_argument('-a', '--address', required=False,
                   help='Yaml file of function addresses, providing it over' +
                   'rides addresses in config file for functions')
    p.add_argument('--log_blocks', default=False, const=True, nargs='?',
                   help="Enables QEMU's logging of basic blocks, options [irq]")
    p.add_argument('-n', '--name', default='HALucinator',
                   help='Name of target for avatar, used for logging')
    p.add_argument('-r', '--rx_port', default=5555, type=int, required=False,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5556, type=int, required=False,
                   help='Port number to send IO messages via zmq')
    p.add_argument('-p', '--gdb_port', default=1234, type=int,
                   help="GDB_Port")
    p.add_argument('-e', '--elf', default=None,
                   help='Elf file, required to use recorder')

    args = p.parse_args()

    logging.basicConfig()
    log = logging.getLogger()
    # log.setLevel(logging.INFO)

    config_path = args.get("config")
    config = Config.load(config_path)
    
    # TODO: deprecate this, but for now leave it alone
    if args.address is not None:
        override_addresses(config, args.address)

    if 'memory_map' not in config:
        if args.memory_config == None:
            log.error("Invalid configuration")
            print("Memory Configuration must be in config file or provided using -m")
            p.print_usage()
            quit(-1)

        # Use memory configuration from mem_config
        base_dir = os.path.split(args.memory_config)[0]
        with open(args.memory_config, 'rb') as infile:
            memyaml = yaml.load(infile, Loader=yaml.FullLoader)
            

        # TODO: better merging strategy here.
        config['memory_map'] = memyaml['memory_map']
        config['peripherals'] = memyaml['peripherals']

    if 'ipc' not in config:

        config['ipc']['rx_port'] = args.rx_port
        config['ipc']['tx_port'] = args.tx_port

    base_dir = os.path.split(args.config)[0]

        

    # TODO force more of this into config.
    emulate_binary(config, base_dir, args.name, args.log_blocks,
                   elf_file=args.elf, gdb_port=args.gdb_port)


if __name__ == '__main__':
    main()
