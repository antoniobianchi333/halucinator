# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC (NTESS). 
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains 
# certain rights in this software.


import zmq
from ..peripheral_models.peripheral_server import encode_zmq_msg, decode_zmq_msg
from .ioserver import IOServer
import logging

log = logging.getLogger("RS232Server")
log.setLevel(logging.WARN)

class RS232PrintServer(object):
    def __init__(self, ioserver):
        self.ioserver = ioserver
        ioserver.register_topic(
            'Peripheral.RS232Publisher.write', self.write_handler)

    def write_handler(self, ioserver, msg):
        stringbytes = msg["data"]
        for sb in stringbytes:
            print("%c" % chr(sb), end='', flush=True)
        #print("%s" % chr(msg["data"]), end=' ', flush=True)

#    def send_data(self, id, chars):
#        d = {'id': id, 'chars': chars}
#        log.debug("Sending Message %s" % (str(d)))
#        self.ioserver.send_msg('Peripheral.RS232Publisher.rx_data', d)


def main(*pargs):
    from argparse import ArgumentParser
    p = ArgumentParser()
    
    p.add_argument('-r', '--rx_port', default=5556,
                   help='Port number to receive zmq messages for IO on')
    p.add_argument('-t', '--tx_port', default=5555,
                   help='Port number to send IO messages via zmq')
    p.add_argument('-i', '--id', default=0x20000ab0, type=int,
                   help="Id to use when sending data")
    args = p.parse_args(*pargs)

    logging.basicConfig()
    #log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    io_server = IOServer(args.rx_port, args.tx_port)
    serialserv = RS232PrintServer(io_server)

    io_server.start()

    try:
        while(1):
            pass
    except KeyboardInterrupt:
        pass
    log.info("Shutting Down")
    io_server.shutdown()
    # io_server.join()


if __name__ == '__main__':
    main()    
