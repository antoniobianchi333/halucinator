#!/bin/bash

set -e

# Detect environment
DISTRO=`awk -F= '/^NAME/{print $2}' /etc/os-release | tr -d '"'`
IN_VENV=$(python -c 'import sys; print ("1" if sys.prefix != sys.base_prefix else "0")')

if (( IN_VENV == 0 )); then
echo "Halcuinator Setup"
echo ""
echo "[!] You are executing this script outside a virtual environment. This is not advised."
echo "    You are advised to create a virtual environment as follows:"
echo ""
echo "virtualenv halenv"
echo "source ./halenv/bin/activate"
echo ""
echo "    Then re-run this script, to avoid polluting your system."
echo "    You can type"
echo ""
echo "deactivate"
echo ""
echo "    at your shell at any point to exit this virtual environment."
echo ""
exit 1
fi


# Pull in everything in vendor, if not already done.
#git submodule update --init --recursive

# keystone-engine is a dependency of avatar, but pip install doesn't build
# correctly on ubuntu
# use angr's prebuilt wheel
pip install https://github.com/angr/wheels/raw/master/keystone_engine-0.9.1.post3-py2.py3-none-linux_x86_64.whl

pushd vendor/avatar2
pip install -e .

#pushd targets
#./build_qemu.sh
#popd
popd


pip install -r requirements.txt
pip install -e .

