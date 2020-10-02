
# Arduino Simple Helloworld Firmware.

This project assumes the Arduino IDE is installed at `/opt/arduino/ide/`
and that [the Arduino Makefile project][arduino-makefile] is checked out at 
`/opt/arduino/arduino-makefile`. 

The file `arduino_helloworld.ino` exists to allow the IDE to see this as a 
sketch folder, but does not contain sourcecode. Instead these are stored in 
`*.cpp` files as usual.

There are two makefiles that perform the same tasks as the IDE:

 * Makefile.atmega328p - targets the Arduino UNO boards.
 * Makefile.atmega2560 - targets the Arduino MEGA 2560 boards.

Both makefiles have the same set of targets:

 - `default`: build.
 - `flash`: program the device available on `MONITOR_PORT`, which defaults to 
   `/dev/ttyACM0`.
 - `serial`, which connects to the serial port and displays output from the 
   device.


    [arduino-makefile]: https://github.com/sudar/Arduino-Makefile
