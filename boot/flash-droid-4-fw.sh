#!/bin/bash
# written by Tony Lindgren <tony@atomide.com>

fastboot=fastboot

$fastboot flash cdt.bin cdt.bin_patch
$fastboot reboot-bootloader
sleep 2
$fastboot flash emstorage emstorage.img
$fastboot reboot-bootloader
sleep 2
$fastboot flash mbm allow-mbmloader-flashing-mbm.bin
$fastboot reboot-bootloader
sleep 2
$fastboot flash mbmloader mbmloader.bin
$fastboot flash mbm mbm.bin
$fastboot oem fb_mode_set
$fastboot reboot-bootloader
sleep 2
$fastboot flash cdt.bin cdt.bin
$fastboot reboot-bootloader
sleep 2
$fastboot erase cache
$fastboot erase userdata
$fastboot flash logo.bin logo.bin
$fastboot flash ebr ebr
$fastboot flash mbr mbr
$fastboot flash devtree device_tree.bin
$fastboot flash boot boot.img
$fastboot flash system system.img
$fastboot flash recovery recovery.img
$fastboot flash cdrom cdrom
$fastboot flash preinstall preinstall.img
$fastboot flash radio radio.img
$fastboot oem fb_mode_clear

echo "Optionally run fastboot erase userdata and cache"
