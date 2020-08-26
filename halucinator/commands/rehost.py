#!/usr/bin/env python

import os
import logging
from argparse import ArgumentParser

import ..config as cfg

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
    p.add_argument('-c', '--config', required=False,
                   help='Config file for halucinator')
    p.add_argument('-p', '--project', required=True,
                   help='Project configuration file used to run emulation')
    p.add_argument('-m', '--memory_config', required=False, default=None,
                   help='Memory Config, will overwrite config in --config if present if memories not in -c this is required')
    p.add_argument('-a', '--address', required=False,
                   help='Yaml file of function addresses, providing it over' +
                   'rides addresses in config file for functions')
    p.add_argument('--log_blocks', default=False, const=True, nargs='?',
                   help="Enables QEMU's logging of basic blocks, options [irq]")
    p.add_argument('-n', '--name', default='HALucinator',
                   help='Name of target for avatar, used for logging')
    p.add_argument('-r', '--rx_port', default=5555, type=int,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5556, type=int,
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
    if config_path == None:
        config_path = 
    

    with open(, 'rb') as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    with open(args.project, 'rb') as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)

    if args.address is not None:
        override_addresses(config, args.address)

    if 'memories' not in config and args.memory_config == None:
        print("Memory Configuration must be in config file or provided using -m")
        p.print_usage()
        quit(-1)

    if args.memory_config:
        # Use memory configuration from mem_config
        base_dir = os.path.split(args.memory_config)[0]
        with open(args.memory_config, 'rb') as infile:
            mem_config = yaml.load(infile, Loader=yaml.FullLoader)
            if 'options' in mem_config:
                config['options'] = mem_config['options']
            config['memories'] = mem_config['memories']
            config['peripherals'] = mem_config['peripherals']
    else:
        base_dir = os.path.split(args.config)[0]

    emulate_binary(config, base_dir, args.name, args.log_blocks,
                   args.rx_port, args.tx_port,
                   elf_file=args.elf, gdb_port=args.gdb_port)


if __name__ == '__main__':
    main()
