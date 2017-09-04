#!/bin/sh

scp -r src/* resources/* pi@192.168.1.212:/home_org/pi/pi-scan
scp -r config/touch.ini pi@192.168.1.212:/home_org/pi/.kivy/config.ini

