import signal
import sys
import functools
import shlex

from halucinator.external_devices.canbus import CANBusDevice, AMP, symbolic_exec_parse
from halucinator.external_devices.MMIOLED import LEDDevice
from halucinator.external_devices.ioserver import IOServer

from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget,
        QPlainTextEdit, QTextEdit,
        QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap
from qasync import QEventLoop

led_names = {
    "led_left_outer": 0,
    "led_left_inner": 1,
    "led_right_inner": 2,
    "led_right_outer": 3
}

led_labels = ["Outer Left", "Inner Left", "Inner Right", "Outer Right"]

ampdevice = None
leddevice = None
candevice = None
candata_reset = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
candata_excessive = [0x00, 0x00, 0xFF, 0xFF, 0x0C, 0x00, 0x00, 0x00]
candata_ok = [0x00, 0x00, 0x32, 0x32, 0x0C, 0x00, 0x00, 0x00]

def can_msg(data):

    idx = 0xFEF1 << 8
    return (idx, data)

class Dashboard(QDialog):

    ledchanged_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):

        # be a good Qt citizen
        super(Dashboard, self).__init__(parent)

        self._createledpanel()
        self._createbtnpanel()
        self._createsymbolicpanel()
        self._createlogpanel()
        layout_main = QGridLayout()
        layout_main.addWidget(self.groupbox_left, 0,0)
        layout_main.addWidget(self.groupbox_right, 0,1)
        layout_main.addWidget(self.groupbox_symbolic, 1,0)
        layout_main.addWidget(self.groupbox_left_lower, 2,0)
        self.setLayout(layout_main)
        self.setWindowTitle("AMP HALucinator Demo")

    def logui(self, text):
        self.logtext.appendPlainText(text)

    @pyqtSlot(int, int)
    def ledevent(self, idx, value):

        ledqlabel = self._ledmap[idx]
        ledgraphic = self._ledmapg[idx]
        ledname = led_labels[idx]

        self.logui("LED Change Event: LED %s Value %d" % (ledname, value))

        vlabel = "Off"
        if value > 10:
            vlabel = "On"
            ico = self.pixmap_ledon
        else:
            vlabel = "Off"
            ico = self.pixmap_ledoff

        lstr = "%s: %s (%d)" % (ledname, vlabel, value)
        ledqlabel.setText(lstr)
        ledgraphic.setPixmap(ico)

    @pyqtSlot()
    def excessivespeed_event(self):
        data = candata_excessive
        
        self.logui("CAN Command: Sending Brake, Excessive Speed")
        self.logui("CAN RAW: %s" % str(data))

        params = can_msg(data)
        candevice.send_data_to_emulator(*params)

    @pyqtSlot()
    def normalspeed_event(self):
        data = candata_ok
        self.logui("CAN Command: Sending Brake, Normal Speed")
        self.logui("CAN RAW: %s" % str(data))
        
        params = can_msg(data)
        candevice.send_data_to_emulator(*params)


    @pyqtSlot()
    def reset_event(self):
        data = candata_reset
        self.logui("CAN Command: Sending Reset Brake")
        self.logui("CAN RAW: %s" % str(data))
        
        params = can_msg(data)
        candevice.send_data_to_emulator(*params)


    @pyqtSlot()
    def send_symbolic(self):
        data = self.txtEntry.text()
         
        def invalid_input(message):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(message)
            msg.setWindowTitle("AMP Halucinator DEMO")
            msg.exec_()
            return
        

        try:
            canframe_s, dashboard_s = shlex.split(data)
        except ValueError:
            invalid_input("Please provide two inputs from symbolic execution: the CAN message frame and constraints for register r1")
            return

        canframe_parsed, err = symbolic_exec_parse(canframe_s)
        if canframe_parsed == None:
            invalid_input(err)
            return

        if len(canframe_parsed) > 8:
            invalid_input('CANBus Data Frames are limited to 8 bytes')
            return
    
        canframe_data = list(map(lambda x: x if x!=None else 0, canframe_parsed))
        while len(canframe_data) < 8:
            canframe_data.append(0)
        
        # canframe data is now valid, next option.
        r1vframe_parsed, err = symbolic_exec_parse(dashboard_s)
        if r1vframe_parsed == None:
            invalid_input(err)
            return

        self.logui("SYMBOLIC Command: Sending")
        self.logui("CAN RAW: %s" % str(canframe_data))
        self.logui("R1-V RAW: %s" % str(r1vframe_parsed))
        self.txtEntry.setText("")

        idx = 0xFEF1 << 8
        ampdevice.set_rxbrake_routine_r1(r1vframe_parsed)
        candevice.send_data_to_emulator(idx, canframe_data)
        return

    @pyqtSlot()
    def clearlog_event(self):
        self.logtext.clear()

    def _createledpanel(self):

        self.pixmap_ledon = QPixmap('res/ledred_on.png')
        self.pixmap_ledoff = QPixmap('res/ledred_off.png')

        self._ledmap = dict()
        self._ledmapg = dict()

        self.groupbox_left = QGroupBox("LED Panel")


        self.led_g_ol = QLabel()
        self.led_g_ol.setPixmap(self.pixmap_ledoff)
        self.led_g_ol.setFixedSize(100, 100)
        self.led_g_ol.setScaledContents(True);
        self.led_g_il = QLabel()
        self.led_g_il.setPixmap(self.pixmap_ledoff)
        self.led_g_il.setFixedSize(100, 100)
        self.led_g_il.setScaledContents(True);
        self.led_g_ir = QLabel()
        self.led_g_ir.setPixmap(self.pixmap_ledoff)
        self.led_g_ir.setFixedSize(100, 100)
        self.led_g_ir.setScaledContents(True);
        self.led_g_or = QLabel()
        self.led_g_or.setPixmap(self.pixmap_ledoff)
        self.led_g_or.setFixedSize(100, 100)
        self.led_g_or.setScaledContents(True);

        self.led_ol = QLabel("Outer Left: Off (1)")
        self.led_il = QLabel("Inner Left: Off (1)")
        self.led_ir = QLabel("Inner Right: Off (1)")
        self.led_or = QLabel("Outer Right: Off (1)")

        self._ledmap[0] = self.led_ol
        self._ledmap[1] = self.led_il
        self._ledmap[2] = self.led_ir
        self._ledmap[3] = self.led_or
        
        self._ledmapg[0] = self.led_g_ol
        self._ledmapg[1] = self.led_g_il
        self._ledmapg[2] = self.led_g_ir
        self._ledmapg[3] = self.led_g_or

        layout_all = QGridLayout()
        layout_all.addWidget(self.led_g_ol, 0, 0)
        layout_all.addWidget(self.led_g_il, 0, 1)
        layout_all.addWidget(self.led_g_ir, 0, 2)
        layout_all.addWidget(self.led_g_or, 0, 3)
        layout_all.addWidget(self.led_ol, 1, 0)
        layout_all.addWidget(self.led_il, 1, 1)
        layout_all.addWidget(self.led_ir, 1, 2)
        layout_all.addWidget(self.led_or, 1, 3)
        self.groupbox_left.setLayout(layout_all)

    def _createbtnpanel(self):

        self.groupbox_right = QGroupBox("Control")
        
        self.btnSpeedOK = QPushButton("Send Normal Speed")
        self.btnSpeedExcessive = QPushButton("Send Excessive Speed")
        self.btnReset = QPushButton("Send Reset Message")

        self.btnClearLog = QPushButton("Clear Log")
        self.btnExit = QPushButton("Exit")

        self.btnSpeedOK.clicked.connect(self.normalspeed_event)
        self.btnSpeedExcessive.clicked.connect(self.excessivespeed_event)
        self.btnReset.clicked.connect(self.reset_event)

        self.btnClearLog.clicked.connect(self.clearlog_event)
        self.btnExit.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addWidget(self.btnSpeedOK)
        layout.addWidget(self.btnSpeedExcessive)
        layout.addWidget(self.btnReset)
        layout.addWidget(self.btnClearLog)
        layout.addWidget(self.btnExit)
        layout.addStretch(1)
        self.groupbox_right.setLayout(layout)
   
    def _createsymbolicpanel(self):
        self.groupbox_symbolic = QGroupBox("Symbolic Execution Input")
        self.txtEntry = QLineEdit("")
        self.btnSendSymbolic = QPushButton("Send Symbolic Input")
        self.btnSendSymbolic.clicked.connect(self.send_symbolic)
        layout = QHBoxLayout()
        layout.addWidget(self.txtEntry, 4)
        layout.addWidget(self.btnSendSymbolic, 1)
        self.groupbox_symbolic.setLayout(layout)

    def _createlogpanel(self):

        self.groupbox_left_lower = QGroupBox("Event Log")
        layout = QVBoxLayout()

        self.logtext = QPlainTextEdit()
        self.logtext.setReadOnly(True)
        layout.addWidget(self.logtext)
        self.groupbox_left_lower.setLayout(layout)

def ledchange(qtsignal, name, value):
    idx = led_names[name]
    qtsignal.emit(idx, value)

def main(*args):

    global ampdevice
    global leddevice
    global candevice

    app = QApplication(*args)

    dashboard = Dashboard()


    ledevent = functools.partial(ledchange, dashboard.ledchanged_signal)

    io_server = IOServer(5556, 5555)
    ampdevice = AMP(io_server)
    leddevice = LEDDevice(io_server, list(led_names.keys()), ledevent)
    candevice = CANBusDevice(io_server)



    # Connect the signal to its slot.
    dashboard.ledchanged_signal.connect(dashboard.ledevent)
    io_server.start()

    dashboard.show()
    try:
        app.exec_()
    except KeyboardInterrupt as k:
        pass
    except Exception as e:
        print("Exception occurred during execution")
        print(e)

    io_server.shutdown()
    io_server.join()

    print("Done.")

if __name__ == '__main__':
    main(sys.argv)

