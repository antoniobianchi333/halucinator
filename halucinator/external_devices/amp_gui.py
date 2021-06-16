
import signal
import sys
import functools

from halucinator.external_devices.canbus import CANBusDevice
from halucinator.external_devices.MMIOLED import LEDDevice
from halucinator.external_devices.ioserver import IOServer

from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget,
        QPlainTextEdit, QTextEdit,
        QVBoxLayout, QWidget)
from qasync import QEventLoop

led_names = {
    "led_left_outer": 0,
    "led_left_inner": 1,
    "led_right_inner": 2,
    "led_right_outer": 3
}

led_labels = ["Outer Left", "Inner Left", "Inner Right", "Outer Right"]

class Dashboard(QDialog):

    ledchanged_signal = pyqtSignal(int, int)

    def __init__(self, parent=None):

        # be a good Qt citizen
        super(Dashboard, self).__init__(parent)

        self._createledpanel()
        self._createbtnpanel()
        self._createlogpanel()
        layout_main = QGridLayout()
        layout_main.addWidget(self.groupbox_left, 0,0)
        layout_main.addWidget(self.groupbox_right, 0,1)
        layout_main.addWidget(self.groupbox_left_lower, 1,0)
        self.setLayout(layout_main)
        self.setWindowTitle("AMP HALucinator Demo")

    def logui(self, text):
        self.logtext.appendPlainText(text)

    @pyqtSlot(int, int)
    def ledevent(self, idx, value):

        ledqlabel = self._ledmap[idx]
        ledname = led_labels[idx]

        self.logui("LED Change Event: LED %s Value %d", ledname, value)

        vlabel = "Off"
        if value > 10:
            vlabel = "On"
        else:
            vlabel = "Off"

        lstr = "%s: %s (%d)" % (ledname, vlabel, value)
        ledqlabel.setWindowTitle(lstr)

    @pyqtSlot()
    def excessivespeed_event(self):
        self.logui("CAN Command: Sending Brake, Excessive Speed")

    @pyqtSlot()
    def normalspeed_event(self):
        self.logui("CAN Command: Sending Brake, Normal Speed")

    @pyqtSlot()
    def reset_event(self):
        self.logui("CAN Command: Sending Reset Brake")

    @pyqtSlot()
    def clearlog_event(self):
        self.logtext.clear()

    def _createledpanel(self):

        self._ledmap = dict()

        self.groupbox_left = QGroupBox("LED Panel")

        self.led_ol = QLabel("Outer Left: Off (1)")
        self.led_il = QLabel("Inner Left: Off (1)")
        self.led_ir = QLabel("Inner Right: Off (1)")
        self.led_or = QLabel("Outer Right: Off (1)")

        self._ledmap[0] = self.led_ol
        self._ledmap[1] = self.led_il
        self._ledmap[2] = self.led_ir
        self._ledmap[3] = self.led_or

        layout = QHBoxLayout()
        layout.addWidget(self.led_ol)
        layout.addWidget(self.led_il)
        layout.addWidget(self.led_ir)
        layout.addWidget(self.led_or)

        layout.addStretch(1)
        self.groupbox_left.setLayout(layout)


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
   
    def _createlogpanel(self):

        self.groupbox_left_lower = QGroupBox("Event Log")
        layout = QVBoxLayout()

        self.logtext = QPlainTextEdit()
        self.logtext.setReadOnly(True)
        layout.addWidget(self.logtext)
        self.groupbox_left_lower.setLayout(layout)

def ledchange(qtsignal, name, value):
    idx = led_names[name]
    qtsignal(idx, value)

def main(*args):

    app = QApplication(*args)

    dashboard = Dashboard()


    ledevent = functools.partial(ledchange, dashboard.ledchanged_signal)

    io_server = IOServer(5556, 5555)
    leddevice = LEDDevice(io_server, list(led_names.keys()), ledevent)
    canbus = CANBusDevice(io_server)

    # Connect the signal to its slot.
    dashboard.ledchanged_signal.connect(dashboard.ledevent)
    io_server.start()

    dashboard.show()
    app.exec_()
    io_server.shutdown()
    io_server.join()

    print("Done.")

if __name__ == '__main__':
    main(sys.argv)
