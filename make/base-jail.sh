#!/bin/sh

# Locales

locale-gen en_US.UTF-8


# Add kivy repo

#echo 'deb http://ppa.launchpad.net/kivy-team/kivy/ubuntu trusty main' >> /etc/apt/sources.list
#apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A863D2D6

apt-get update && apt-get -y upgrade

# Python Basics, general utilitites, external storage, camera stuff
apt-get -y --force-yes install \
  python-setuptools python-dev pkg-config cython python-pip build-essential python-pil \
  git-core \
  dbus python-dbus udisks2 \
  liblua5.2-0 lua5.2 liblua5.2-dev libusb-dev

  # General utilities
  #sudo curl ca-certificates binutils
  #echo 'pi ALL=NOPASSWD: /sbin/shutdown' >> /etc/sudoers

# Camera Stuff

pip install lupa --install-option="--no-luajit"

# Foot Pedal

apt-get -y --force-yes install wiringpi
pip install wiringpi

# Kivy

apt-get clean

apt-get -y --force-yes install \
   libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
   pkg-config libgl1-mesa-dev libgles2-mesa-dev \
   libgstreamer1.0-dev \
   gstreamer1.0-plugins-{bad,base,good,ugly} \
   gstreamer1.0-{omx,alsa} python-dev cython
apt-get -y --force-yes install libmtdev1

pip install git+https://github.com/kivy/kivy.git@master

apt-get clean


# Setup User

#mkdir /home/pi
#cp /etc/skel/.* /home/pi
#chown pi /home/pi /home/pi/.*

# Read only

apt-get -y --force-yes install \
  unionfs-fuse

dphys-swapfile swapoff
dphys-swapfile uninstall
systemctl disable dphys-swapfile 
