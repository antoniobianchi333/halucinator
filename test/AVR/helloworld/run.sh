#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

halucinator-rehost -c=./test/AVR/helloworld/arduino_helloworld_config.yaml \
  -a=test/AVR/helloworld/arduino_helloworld_addrs.yaml \
  -m=test/AVR/helloworld/arduino_helloworld_memory.yaml --log_blocks=irq -n Arduino_Example
