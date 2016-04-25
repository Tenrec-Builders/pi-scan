#!/bin/sh

cd /home/pi/chdkptp.py
git submodule init
git submodule update
pip install .

# Make sure everything is owned by the pi user

chown -R pi /home/pi

