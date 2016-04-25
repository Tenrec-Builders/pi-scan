#!/bin/sh

cp work/base.img work/installed.img

sudo mount work/installed.img -o loop,offset=67108864,rw -t ext4 mnt
sudo mount work/installed.img -o loop,offset=4194304,rw mnt/boot

sudo mv mnt/etc/ld.so.preload  mnt/etc/ld.so.preload.backup

################################################
# Copy Files
################################################

# Setup boot configuration

sudo cp files/config.txt mnt/boot/config.txt

# Read only filesystem

sudo cp files/mount_unionfs mnt/usr/local/bin/mount_unionfs
sudo cp files/fstab mnt/etc/fstab 


# udisks2 permissions

sudo cp files/55-udisks2.pkla mnt/etc/polkit-1/localauthority/50-local.d/55-udisks2.pkla

# udev rules

sudo cp files/99-usb.rules mnt/etc/udev/rules.d/99-usb.rules

# prevent screen blanking

sudo cp files/kbd-config mnt/etc/kbd/config

################################################
# Installation
################################################

# Pi Scan

sudo mkdir -p mnt/home/pi/pi-scan
sudo cp -r ../src/* mnt/home/pi/pi-scan
sudo cp -r ../resources/spinner.gif mnt/home/pi/pi-scan

# For Touch Screen

sudo mkdir -p mnt/home/pi/.kivy
sudo cp -r ../config/touch.ini mnt/home/pi/.kivy/config.ini

sudo cp files/rc.local mnt/etc/rc.local

# chdkptp
# TODO Un-hardcode chdkptp.py location
sudo mkdir -p mnt/home/pi/chdkptp.py
sudo cp -r ~/git/chdkptp.py mnt/home/pi/

sudo cp install-jail.sh mnt
cd mnt
sudo chroot . ./install-jail.sh
cd ..
sudo rm mnt/install-jail.sh

################################################
# Cleanup
################################################

sudo mv mnt/etc/ld.so.preload.backup  mnt/etc/ld.so.preload

################################################
# Implement final readonly changeover
################################################

sudo cp -al mnt/etc mnt/etc_org
sudo mv mnt/var mnt/var_org
sudo mv mnt/home mnt/home_org
sudo mv mnt/media mnt/media_org
sudo mkdir mnt/etc_rw
sudo mkdir mnt/var mnt/var_rw
sudo mkdir mnt/home mnt/home_rw
sudo mkdir mnt/media mnt/media_rw


sudo umount mnt/boot
sudo umount mnt
