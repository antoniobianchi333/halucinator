#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

DIR=$(pwd)/test/AMP/ch2-stm32-purdue/
halucinator-rehost \
  -c=$DIR/nucleo32-purdue_config.yaml \
  -a=$DIR/nucleo32-purdue_addrs.yaml \
  -m=$DIR/nucleo32-purdue_memory.yaml --log_blocks=irq \
  -n AMP-C2-PURDUE
