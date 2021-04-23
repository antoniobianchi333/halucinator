#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

DIR=$(pwd)/test/AMP/ch2-stm32-patched/
halucinator-rehost \
  -c=$DIR/nucleo32-patched_config.yaml \
  -a=$DIR/nucleo32-patched_addrs.yaml \
  -m=$DIR/nucleo32-patched_memory.yaml --log_blocks=irq \
  -n AMP-C2-PATCHED
