
import signal
import sys
import functools

from .canbus import CANBusDevice
from .MMIOLED import LEDDevice

from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget)
from asyncqt import QEventLoop

led_names = {
    "led_left_outer": 0,
    "led_left_inner": 1,
    "led_right_inner": 2,
    "led_right_outer": 3
}

led_labels = ["Outer Left", "Inner Left", "Inner Right", "Outer Right"]

class Dashboard(QDialog):

    def __init__(self, parent=None):

        # be a good Qt citizen
        super(Dashboard, self).__init__(parent)

        self._createledpanel()
        self._createbtnpanel()
        layout_main = QGridLayout()
        layout_main.addWidget(self.groupbox_left, 0,0)
        layout_main.addWidget(self.groupbox_right, 0,1)
        self.setLayout(layout_main)
        self.setWindowTitle("AMP HALucinator Demo")

    @QtCore.pyqtSlot(int, int)
    def ledevent(self, idx, value):

        ledqlabel = self._ledmap[idx]
        ledname = led_labels[idx]
        vlabel = "Off"
        if value > 10:
            vlabel = "On"
        else:
            vlabel = "Off"

        lstr = "%s: %s (%d)" % (ledname, vlabel, value)
        ledqlabel.setWindowTitle(lstr)

    def _createledpanel(self):

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
        
        btnSpeedOK = QPushButton("Send Normal Speed")
        btnSpeedExcessive = QPushButton("Send Excessive Speed")
        btnReset = QPushButton("Send Reset Message")

        layout = QVBoxLayout()
        layout.addWidget(btnSpeedOK)
        layout.addWidget(btnSpeedExcessive)
        layout.addWidget(btnReset)
        layout.addStretch(1)
        self.groupbox_right.setLayout(layout)
    

def ledchange(qtsignal, name, value):
    idx = led_names[name]


def main():

    app = QApplication(sys.argv)

    dashboard = Dashboard()

    ledchanged_signal = QtCore.pyqtSignal(str, int)
    ledevent = functools.partial(ledchange, ledchanged_signal)

    leddevice = LEDDevice(io_server, list(led_names.keys()), ledevent)
    canbus = CANBusDevice(io_server)

    # Connect the signal to its slot.
    ledchanged_signal.connect(dashboard.ledevent)
    io_server.start()

    dashboard.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
