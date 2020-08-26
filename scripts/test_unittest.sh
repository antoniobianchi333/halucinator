#!/bin/sh

IN_VENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

if (( IN_VENV == 0 )); then
source halenv/bin/activate
fi
nosetests halucinator -v
