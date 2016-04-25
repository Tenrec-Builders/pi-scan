#!/bin/sh

cp $1 work/base.img

# Offsets based on fdisk -lu
sudo mount work/base.img -o loop,offset=67108864,rw -t ext4 mnt
#sudo mount work/base.img -o loop,offset=4194304,rw mnt/boot

#sudo mount --bind /dev mnt/dev/
#sudo mount --bind /sys mnt/sys/
#sudo mount --bind /proc mnt/proc/
#sudo mount --bind /dev/pts mnt/dev/pts

sudo mv mnt/etc/ld.so.preload  mnt/etc/ld.so.preload.backup

sudo cp /usr/bin/qemu-arm-static mnt/usr/bin/

# Locale configuration

sudo cp files/locale mnt/etc/default/locale
sudo cp files/locale.gen mnt/etc/locale.gen

################################################
# Chroot Commands
################################################

sudo cp base-jail.sh mnt
cd mnt
sudo chroot . ./base-jail.sh
cd ..
sudo rm mnt/base-jail.sh

# Cleanup

sudo mv mnt/etc/ld.so.preload.backup  mnt/etc/ld.so.preload

#sudo umount mnt/dev/pts
#sudo umount mnt/dev
#sudo umount mnt/sys
#sudo umount mnt/proc
#sudo umount mnt/boot
sudo umount mnt

#cp work/base.img work/installed.img
