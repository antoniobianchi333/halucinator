#! /bin/bash

#source ~/.virtualenvs/halucinator/bin/activate

DIR=$(pwd)/test/AMP/ch2-stm32-vuln/
halucinator-rehost \
  -c=$DIR/nucleo32-vuln_config.yaml \
  -a=$DIR/nucleo32-vuln_addrs.yaml \
  -m=$DIR/nucleo32-vuln_memory.yaml --log_blocks=irq \
  -n AMP-C2-VULN
