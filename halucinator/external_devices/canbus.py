
from collections import deque, defaultdict
import logging
import cmd2
import zmq
import json
from ..peripheral_models.peripheral_server import encode_zmq_msg, decode_zmq_msg
from .ioserver import IOServer

log = logging.getLogger("CanServer")
log.setLevel(logging.DEBUG)

def symbolic_exec_parse(s):

    if s[0] != "[" or s[-1:] != "]":
        return (None, 'Symbolic exec output should be surrounded by []')

    s_inner = s[1:-1]
    elements = s_inner.replace(" ","").split(",")

    results = list()

    for element in elements:
        element = element.replace("'", "")
        if element == '?':
            results.append(None)
            continue

        try:
            eint = int(element)
        except ValueError:
            return (None, 'Symbolic execution must output data [a,b,c,d] where each element is a numeric value, or ?')

        results.append(eint)

    return (results, '')

class AMP(object):

    def __init__(self, ioserver):
        self.ioserver = ioserver

    def set_rxbrake_routine_r1(self, values):
        
        d = {'data': values}
        self.ioserver.send_msg('Peripheral.AMP.rx_data', d)



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

    def __init__(self, candev, ampdev, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candev = candev
        self.ampdev = ampdev
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

    def do_amp_can_badspeed(self, args):
        'AMP: Send CAN message corresponding to break message'
        
        # send the break message expected by the firmware

        #speed value is int16_t
        #speed_value  = (buff[3] << 8) + buff[2];  // buf[3] = speed integer, buf[2] = speed decimal
        #brake_switch = (buff[4] & 0b00001100) >> 2

        # set speed value to 0x80 << 8 + 00 = -32768.
        # set brake_switch to true.

        #       0     1     2     3     4     5     6     7
        data = [0x00, 0x00, 0xFF, 0xFF, 0x0C, 0x00, 0x00, 0x00]

        # cruise control vehicle speed setting:
        # PGN_CruiseControlVehicleSpeed1     0xFEF1
        # #define CAN_RX_FIFO0                (0x00000000U)

        idx = 0xFEF1 << 8

        print("Sending speed that will decode to 65535 (uint16)/-32768 (int16)")

        self.candev.send_data_to_emulator(idx, data)
    
    def do_amp_can_goodspeed(self, args):
        'AMP: Send CAN message corresponding to break message'
        
        # send the break message expected by the firmware

        #speed value is int16_t
        #speed_value  = (buff[3] << 8) + buff[2];  // buf[3] = speed integer, buf[2] = speed decimal
        #brake_switch = (buff[4] & 0b00001100) >> 2

        # set speed value to 0x80 << 8 + 00 = -32768.
        # set brake_switch to true.

        #       0     1     2     3     4     5     6     7
        data = [0x00, 0x00, 0x32, 0x32, 0x0C, 0x00, 0x00, 0x00]

        # cruise control vehicle speed setting:
        # PGN_CruiseControlVehicleSpeed1     0xFEF1
        # #define CAN_RX_FIFO0                (0x00000000U)

        idx = 0xFEF1 << 8

        print("Sending speed that will decode to 0x3232 (50.50) (OK for int16)")

        self.candev.send_data_to_emulator(idx, data)


    def do_amp_symbolic(self, args):
        'Send input from symbolic execution'

        argv = args.argv
        if len(argv) != 3:
            print("Please supply two arguments: canbus data frame and value for second argument")
            return

        canframe_s = argv[1]
        dashboard_s = argv[2]

        canframe_parsed, err = symbolic_exec_parse(canframe_s)
        if canframe_parsed == None:
            print(err)
            return

        if len(canframe_parsed) > 8:
            print('CANBus Data Frames are limited to 8 bytes')
            return
    
        canframe_data = list(map(lambda x: x if x!=None else 0, canframe_parsed))
        while len(canframe_data) < 8:
            canframe_data.append(0)
        
        # canframe data is now valid, next option.
        r1vframe_parsed, err = symbolic_exec_parse(dashboard_s)
        if r1vframe_parsed == None:
            print(err)
            return

        idx = 0xFEF1 << 8
        self.ampdev.set_rxbrake_routine_r1(r1vframe_parsed)
        self.candev.send_data_to_emulator(idx, canframe_data)
        
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
    ampdev = AMP(io_server)
    io_server.start()

    try:
        CanShell(canbus, ampdev).cmdloop()
    except KeyboardInterrupt:
        pass
    print("")
    print("Shutting down device...", end='')

    canbus.ioserver.shutdown()
    canbus.ioserver.join()
    print("Done.")


if __name__ == '__main__':
    main()
