#!/bin/sh

scp -r src/* resources/* pi@192.168.2.232:/home_org/pi/pi-scan
scp -r config/mouse.ini pi@192.168.2.232:/home_org/pi/.kivy/config.ini

