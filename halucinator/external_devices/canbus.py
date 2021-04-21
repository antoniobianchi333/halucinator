
from collections import deque, defaultdict
import logging
import cmd2
import zmq
from ..peripheral_models.peripheral_server import encode_zmq_msg, decode_zmq_msg
from .ioserver import IOServer

log = logging.getLogger("CanServer")
log.setLevel(logging.DEBUG)

class CANBusDevice(object):

    received_messages = defaultdict(deque)

    def __init__(self, ioserver):
        self.ioserver = ioserver
        self.ioserver.register_topic(
            'Peripheral.CanBus.write', self.tx_handler)

    def rx_handler(self, idx, msg):
        """ 
        Peripheral Server -> Emulator (emulated device receives)
        Here we send messages to the IO Server 
        """
        d = {'id': idx, 'data': msg}
        log.debug("Sending Message %s" % (str(d)))
        
        # We send to rx_data in the model, which adds to the rx_queue and 
        # may be handled with calls to read.
        self.ioserver.send_msg('Peripheral.CanBus.rx_data', d)
    
    def tx_handler(self, ioserver, msg):
        """ 
        Emulator -> Peripheral Server emulated device sends)
        Here we handle messages received from the virtual peripheral.
        We don't transmit here, the naming matches peripheral_models.
        """
        # This function "receives" fropm the perspective of this 
        # emulated device, and is transmission from the perspective of the 
        # emulator.

        can_id = msg['id']
        can_payload = msg['data']
        received_messages[can_id].push(can_payload)

    def send_data_to_emulator(self, canid, data):
        
        if len(data)!= 8:
            print("")
            print("Data is not valid: please only send 8 bytes of data")

        self.rx_handler(canid, data)


    def clear_rx_queue(self, idx=None):
        if idx is not None: 
            queue = self.received_messages.get(idx)
            if queue is not None:
                received_messages[idx].clear()
        else:
            for k in self.received_messages.keys():
                received_messages[k].clear()


class CanShell(cmd2.Cmd):
    intro = 'CAN Device Emulator for AMP'
    prompt = '[CAN] '
    candev = None



    def __init__(self, candev, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.candev = candev
        self.hidden_commands.append('EOF')

    def __parse__(arg):
        return tuple(map(int, arg.split()))

    def can_exit(self):
        return True

    def do_recv(self, args):
        'Return received messsages in a specified queue'
        pass        

    def do_clearrx(self, args):
        'Clear a specified queue'
        # TODO: allow selecting queue to clear.
        self.candev.clear_rx_queue()     

    def do_amp_sendbreak(self, args):
        'AMP: Send CAN message corresponding to break message'
        
        # send the break message expected by the firmware

        #speed value is int16_t
        #speed_value  = (buff[3] << 8) + buff[2];  // buf[3] = speed integer, buf[2] = speed decimal
        #brake_switch = (buff[4] & 0b00001100) >> 2

        # set speed value to 0x80 << 8 + 00 = -32768.
        # set brake_switch to true.

        #       0     1     2     3     4     5     6     7
        data = [0x00, 0x00, 0x00, 0x80, 0x0C, 0x00, 0x00, 0x00]

        # cruise control vehicle speed setting:
        # PGN_CruiseControlVehicleSpeed1     0xFEF1
        # #define CAN_RX_FIFO0                (0x00000000U)

        idx = 0xFEF1 << 8

        self.candev.send_data_to_emulator(idx, data)

    def do_exit(self, args):
        'Exit the virtual CAN device'
        return True

    do_EOF = do_exit
    help_EOF = ''

def main(*args):
    #from argparse import ArgumentParser
    #p = ArgumentParser()
    #p.add_argument('-r', '--rx_port', default=5556,
    #               help='Port number to receive zmq messages for IO on')
    #p.add_argument('-t', '--tx_port', default=5555,
    #               help='Port number to send IO messages via zmq')
    #p.add_argument('-i', '--id', default=0x20000ab0, type=int,
    #               help="Id to use when sending data")
    #args = p.parse_args()

    logging.basicConfig()
    #log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    io_server = IOServer(5556, 5555)
    #io_server = IOServer(args.rx_port, args.tx_port)
    canbus = CANBusDevice(io_server)

    io_server.start()

    try:
        CanShell(canbus).cmdloop()
    except KeyboardInterrupt:
        pass
    print("")
    print("Shutting down device...", end='')

    canbus.ioserver.shutdown()
    canbus.ioserver.join()
    print("Done.")


if __name__ == '__main__':
    main()
