# Pi Scan Overview

Pi Scan is a simple and robust camera controller for book scanners. It was designed to work with the [Archivist book scanner](http://diybookscanner.org/archivist). For questions or help, visit the [forum](http://diybookscanner.org/forum) or email help at tenrec dot builders.

# Requirements

* Raspberry Pi 2
* Two cameras (Canon PowerShot A2500 or Canon PowerShot ELPH 160 (aka IXUS 160))
* Three 4GB SD Cards (2 for cameras, 1 for Pi). One needs to be micro (for the Pi). The other two need to be standard sized or have adapters.
* Mouse, Screen, Optional Keyboard

Plus either

* SD Card Reader
* Fast SD Card for storing scans

Or

* USB Thumb Drive

# Download

Raspberry Pi 2 (for use with mouse):

* [Raspberry Pi 2 Image (for mouse)](http://tenrec.builders/pi-scan/latest/pi-scan-latest-mouse.zip)

Two models of cameras are supported. Download the appropriate image for your camera:

* [Canon PowerShot A2500 Image](http://tenrec.builders/pi-scan/latest/pi-scan-camera-a2500-latest.zip)
* [Canon PowerShot ELPH/IXUS 160 image](http://tenrec.builders/pi-scan/latest/pi-scan-camera-elph160-latest.zip)

Use these images at your own risk. These images may damage your camera. During early testing of the ELPH 160 image, one camera was bricked and the root cause of this problem was never definitively found. See [this link](http://chdk.setepontos.com/index.php?topic=12321.140).

# Installation

The software is packaged as whole disk images which need to be flashed onto SD cards of at least 4GB in size. Because nothing is stored on these images, the speed of the card doesn't matter.

Extract the images from the archives and use an appropriate tool to write them to the cards. Do not just copy the file onto the card. This will not work and you will be sad. If you are updating the camera cards, they may be locked. Before imaging them, you must unlock them. The little switch on the left must be in the *top* position.

Image Writing Tutorials:

* [Windows](https://www.raspberrypi.org/documentation/installation/installing-images/windows.md)
* [Mac](https://www.raspberrypi.org/documentation/installation/installing-images/mac.md)
* [Linux](https://www.raspberrypi.org/documentation/installation/installing-images/linux.md)

## Writing an SD Card on Windows

You will need:

* Win32 Disk Imager ([link](http://sourceforge.net/projects/win32diskimager/))
* An SD Card Reader
* An SD Card (make sure the SD card is unlocked. The little switch on the left must be in the *top* position)
* A disk image downloaded from a location above
* At least 4GB of free disk space

The image you downloaded starts out as a compressed ZIP file. Right-click on it and select 'Extract all...' from the menu.

Pick a destination folder for the extracted file.

Insert SD Card into SD Card Reader.

Run Win32 Disk Imager. You will be asked if you want to allow it to make changes, click yes.

Inside of Win32 Disk Imager, click the little folder and find the image file you extracted before. Select it and click OK.

Select the drive where the SD card is mounted in the 'device' dropdown. Open up 'My Computer' or 'File Explorer' and verify that this is the correct drive.

Click the 'Write' button. This will delete everything on the card and write out the contents of the image out to the drive. So be absolutely sure you are writing to the place you think you are.

## Using SD Cards

Once the images are installed, you will have three SD cards. One needs to be inserted into your Raspberry Pi 2. The other cards are for your cameras. The camera cards must now be locked. The little switch on the left must be in the *bottom* position.

When you turn on the cameras, a CHDK splash screen will briefly appear. This is how you know that everything went ok. If you do not see the splash screen, the cards are not locked or there was some other problem imaging the cards.

Sometimes when you turn on the cameras, a screen appears asking you to set the time and timezone. This will happen the first time you turn on the cameras, or if they have been unplugged for a long time. If this happens, disconnect the USB cable from the camera, use the keypad to set the date and time and dismiss these screens, then replug in the USB cable.

Plug the cameras into the Pi. Plug the SD card reader into the Pi. Plug a monitor, mouse, and (optional) keyboard into the Pi. Turn on the Pi. Note that there is no network mode for this software. It operates by directly connecting I/O devices into the Pi.

# Usage

For an overview of how to use Pi Scan, see the [tutorial video](https://vimeo.com/150385938).

The Pi Scan operating system is completely read only. Everything is saved onto an external SD card that you can put into the SD card reader. Debug logs, configuration, and the actual scanned images all end up there. Whenever you go back to the start screen, Pi Scan will unmount the disk in the card reader so you can remove it safely or turn off the Pi.

There are many camera settings which are not yet user-configurable. These settings are set to values which assume you are using an Archivist book scanner.

## Scanning Steps

1. Boot up the Raspberry Pi and after it starts, you will see the starting screen. When on this screen, Pi Scan will eject your external disk so you can remove it. You can also quit to console and log in using the username 'pi' and password 'raspberry'. For most users, this won't be necessary.
1. On the disk configuration page, Pi Scan searches for and mounts your external storage. The external storage is used for configuration, debugging logs, and it is where the scanned images are saved. Plug in your USB drive or SD Card Reader and SD Card. After a few seconds, your drive will be detected and you will be able to tap next. If your drive is not detected, try unplugging and replugging in the device.
1. On the camera configuration page, Pi Scan searches for two cameras attached via USB to the Pi. Once it finds them, you will be able to optionally set the zoom level or move on to the next step.
1. (Optional) Zoom settings can be set for each camera individually. Tap test shot to capture a photo from each camera and then adjust the zoom settings in the upper left and upper right corners. Don't worry if the pages are on the wrong side for now. When you've set the zoom level you like, tap done. The zoom setting is saved to the external storage, so as long as you keep using the same card, you won't have to re-adjust the zoom settings.
1. In order to keep consistent focus, Pi Scan will auto-focus once in each session and then lock that focus for the remainder of the shots. In order to get the best focus shot, you will want to press two pages against the platen of your scanner just as if you were scanning them and then tap the 'Refocus'. Verify on the preview that the focus is good. You will also want to verify that the 'odd' page is pointing to an odd numbered page in your book and that the 'even' page is pointing to an even numbered page. If they are not, you can tap swap to swap the two pages. This will ensure that the pages are interleaved properly when scanning.
1. During scanning, press pages agains the platen and tap the 'Capture' button. After hearing the shutters on the camera, you can flip to the next page while Pi Scan is processing the photos. On your first scan, you will want to verify that everything looks good. And you will want to do the same periodically as you scan. If you notice a problem during the scan, you can recapture the last two pages with the 'Rescan' button.
1. Once scanning is complete, tap 'Done' which will take you back to the start screen. Then you can remove your external storage and move the files from it to your computer. If you are scanning the same book in multiple sessions, Pi Scan will continue numbering images where you left off. If you move all of the images from the external storage, it will start saving at '0000.jpg' again.

## Handling Failures

In an ideal world, we wouldn't have to deal with this. There are a few ways in which things can go wrong. Pi Scan was designed to be robust in the presence of problems. Each time you see an error, you should be able to get back to scanning with a minimal of fuss. And the error logs and messages it shows should help diagnose any problems you do encounter.

### Capture Failure

Sometimes a camera might return an empty photograph or otherwise not capture successfully. When this happens, Pi Scan will notify you and neither camera image will be saved to disk. Tap 'Ok' on the notification and then tap 'Capture' to try again. If you notice this happening more frequently, note down the error that you see and notify help at tenrec dot builders about the issue. Occasionally, a camera might get into a bad state where every attempted capture fails. If a few captures in a row fail, try turning off and on the camera by hand.

### Camera Crash

Occasionally, a camera will crash or get disconnected. Pi Scan cannot tell the difference between these two events so it always assume that getting disconnected is a crash. When Pi Scan thinks there has been a crash, it pops up a camera debug screen. It will tell you which camera is disconnected, and the last thing it was trying to do when it happened. Reconnect or power cycle the camera and it will detect that the camera is back online. When the camera is back, you can tap 'Get Debug Log' and it will save the debug log for the most recent crash to your external storage in the debug directory. You can send this debug log and the error message you saw on the debug screen to help at tenrec dot builders.

Once all cameras are connected again, you can tap 'Ok' to get back to scanning. You will need to go through the 'refocus' screen again first to make sure that the focus is set properly.

### Pi Scan Crash

Hopefully you will never see a situation where Pi Scan itself crashes, but if you do there is a special crash debug page which shows what happened. Send a photograph of this page to help at tenrec dot builders so it can get fixed.

### Error Log

An error log is saved to the removable storage of every camera failure and crash. This means that even if you tap Ok quickly and miss the message, you can still go back and get it. If you are getting persistent failures or problems, it is worth sending this error log to help at tenrec dot builders.

### Rebooting

Always rememeber that you cannot corrupt Pi Scan by rebooting. So if there is ever any problem or the system stops responding, you can always just unplug and replug the Raspberry Pi and then get back to scanning. If you do this, you will want to double check to make sure the scans you have saved on external storage are good because it will not have been unmounted cleanly.

# After Capture

Pi Scan does just one part of the overall scanning workflow: managing capture. After using Pi Scan, you will have an SD card full of consecutively named JPEG files. Turning those files into an e-book is a process called Post Processing. There are many different kinds of software that can help you do this task. A good open source option is called ScanTailor.

# Version Notes

- 0.7 -- Added page numbers during capture. Fixed ISO and shutter speed settings. Attempt to fix camera crashes when entering alt mode. Add Pi Scan crash detection for preview and camera threads.
- 0.6 -- Fixed preview rotation. Images were being shown upside down.
- 0.5 -- Fixed page numbering issues. Added zoom adjustment UI.
- 0.4 -- Detect when the /debug and /images directories fail to get created and note the problem in the storage screen.
- 0.3 -- Add more crash detection and a screen which displays the error in case of unexpected exceptions
- 0.2 -- Fix issues with spaces in path names and when writing error logs.
- 0.1 -- Initial release
