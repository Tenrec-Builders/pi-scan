# pi-scan

Pi Scan is a simple and robust controller for book scanners. It was designed to work with the [Archivist book scanner](http://diybookscanner.org/archivist). For questions or help, visit the [forum](http://diybookscanner.org/forum) or email help at tenrec dot builders.

# Requirements

* Raspberry Pi 2
* Two cameras (Canon PowerShot A2500 or Canon PowerShot ELPH 160 (aka IXUS 160))
* Three 4GB SD Cards (2 for cameras, 1 for Pi). One needs to be micro (for the Pi). The other two need to be standard sized or have adapters.
* SD Card Reader
* Fast SD Card for storing scans

# Download

Raspberry Pi 2 (for use with mouse):

* [Raspberry Pi 2 Image (for mouse)](http://tenrec.builders/pi-scan/latest/pi-scan-latest-mouse.zip)

Two models of cameras are supported. Download the appropriate image for your camera:

* [Canon PowerShot A2500 Image](http://tenrec.builders/pi-scan/latest/pi-scan-camera-a2500-latest.zip)
* [Canon PowerShot ELPH/IXUS 160 image](http://tenrec.builders/pi-scan/latest/pi-scan-camera-elph160-latest.zip)

# Installation

The software is packaged as whole disk images which need to be flashed onto SD cards of at least 4GB in size. Because nothing is stored on these images, the speed of the card doesn't matter.

Extract the images from the archives and use an appropriate tool to write them to the cards. Do not just copy the file onto the card. This will not work and you will be sad.

Image Writing Tutorials:

* [Windows](https://www.raspberrypi.org/documentation/installation/installing-images/windows.md)
* [Mac](https://www.raspberrypi.org/documentation/installation/installing-images/mac.md)
* [Linux](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md)

Once the images are installed, you will have three SD cards. One needs to be inserted into your Raspberry Pi 2. The other two can be inserted into your cameras.

Plug the cameras into the Pi. Plug the SD card reader into the Pi. Plug a monitor, mouse, and (optional) keyboard into the Pi. Turn on the Pi. Note that there is no network mode for this software. It operates by directly connecting I/O devices into the Pi.

# Usage

For an overview of how to use Pi Scan, see the [tutorial video](https://vimeo.com/150385938).

The Pi Scan operating system is completely read only. Everything is saved onto an external SD card that you can put into the SD card reader. Debug logs, configuration, and the actual scanned images all end up there. Whenever you go back to the start screen, Pi Scan will unmount the disk in the card reader so you can remove it safely or turn off the Pi.

There are many camera settings which are not yet user-configurable. These settings are set to values which assume you are using an Archivist book scanner.

# Version Notes

0.1 -- Initial release
