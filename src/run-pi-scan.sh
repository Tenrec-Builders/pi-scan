#!/bin/sh

sudo sh -c "TERM=linux setterm -blank 0 >/dev/tty0"

while true; do
  cd /home/pi/pi-scan
  python main.py
done;
