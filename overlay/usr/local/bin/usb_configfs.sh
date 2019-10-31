#!/bin/sh

# Change for your UDC controller
phy_module="phy_cpcap_usb"
udc_glue_module="omap2430"
udc_module=musb_hdrc
# musb-hdrc.1.auto
mass_storage_backend=$2 #/dev/mmcblk0p3

modprobe libcomposite > /dev/null 2>&1
	
udc_load_modules() {
	modprobe $udc_module
	modprobe $phy_module
	modprobe $udc_glue_module
}
udc_configure() {
	ifconfig usb0 hw ether de:ab:6a:7a:fc:0b
	ifconfig usb0 10.0.1.2 netmask 255.255.255.0 up
	route add default gw 10.0.1.1
}

udc_pm_test() {
	echo
	echo "Checking blocking bits:"
	grep cm_idlest /sys/kernel/debug/pm_debug/count
	echo
}

start_usb_gadgets() {
	vendor=0x1d6b
	product=0x0106
	file=$1

	if ! mountpoint -q /sys/kernel/debug/; then
		mount -t debugfs none /sys/kernel/debug  
	fi
if ! mountpoint -q /sys/kernel/debug/; then echo true;fi
	if ! mountpoint -q /sys/kernel/config/; then
		mount -t configfs none /sys/kernel/config
	fi

	if [ ! -d /sys/kernel/config/usb_gadget/g1 ]; then
		mkdir /sys/kernel/config/usb_gadget/g1
	fi
	old_pwd=$(pwd)
	cd /sys/kernel/config/usb_gadget/g1
	
	echo $product > idProduct
	echo $vendor > idVendor
	mkdir strings/0x409
	echo 123456789 > strings/0x409/serialnumber
	echo foo > strings/0x409/manufacturer
	echo "Multi Gadget" > strings/0x409/product
	
	mkdir configs/c.1
	echo 100 > configs/c.1/MaxPower
	mkdir configs/c.1/strings/0x409
	echo "Config 100mA" > configs/c.1/strings/0x409/configuration
	
	mkdir configs/c.5
	echo 500 > configs/c.5/MaxPower
	mkdir configs/c.5/strings/0x409
	echo "Config 500mA" > configs/c.5/strings/0x409/configuration

	mkdir functions/mass_storage.0
	echo 1 > functions/mass_storage.0/stall
	echo 0 > functions/mass_storage.0/lun.0/cdrom
	echo 0 > functions/mass_storage.0/lun.0/ro
	echo 0 > functions/mass_storage.0/lun.0/nofua
	echo $file > functions/mass_storage.0/lun.0/file
	ln -s functions/mass_storage.0 configs/c.1
	ln -s functions/mass_storage.0 configs/c.5

#	mkdir functions/acm.0
#	ln -s functions/acm.0 configs/c.1
#	ln -s functions/acm.0 configs/c.5

	mkdir functions/ecm.0
	ln -s functions/ecm.0 configs/c.1
	ln -s functions/ecm.0 configs/c.5

	# Adding rndis seems to cause alignment trap or some
	# random oops on reboot after rmmod udc_glue

	start_udc
	cd $old_pwd
	udc_pm_test
	udc_configure
}
start_udc() {
	udc_name=$(find /proc/irq | grep musb-hdrc | head -n1 | cut -d'/' -f5)
	echo "Using UDC $udc_name"
	echo $udc_name > /sys/kernel/config/usb_gadget/g1/UDC
}

stop_usb_gadgets() {
	old_pwd=$(pwd)
	cd /sys/kernel/config/usb_gadget/g1

	echo "" > /sys/kernel/config/usb_gadget/g1/UDC

	rm configs/c.1/ecm.0
	rm configs/c.5/ecm.0
	rmdir functions/ecm.0

#	rm configs/c.1/acm.0
#	rm configs/c.5/acm.0
#	rmdir functions/acm.0

	echo "" > functions/mass_storage.0/lun.0/file
	rm configs/c.1/mass_storage.0
	rm configs/c.5/mass_storage.0
	rmdir functions/mass_storage.0

	cd $old_pwd

	udc_pm_test
}

udc_unload_modules() {
	rmmod $udc_glue_module
	rmmod $phy_module
	rmmod $udc_module
	udc_pm_test
}
case $1 in
	load)
	udc_load_modules
	;;
	unload)
	udc_unload_modules
	;;
	reload)
	udc_unload_modules
	udc_load_modules
	;;
	start)
	udc_load_modules
	start_usb_gadgets $mass_storage_backend
        ;;
	stop)
	stop_usb_gadgets
	udc_unload_modules
	;;
	restart)
	stop_usb_gadgets
	udc_unload_modules
	udc_load_modules
	start_usb_gadgets $mass_storage_backend
	;;
	configure)
	start_usb_gadgets $mass_storage_backend
	;;
	unconfigure)
	stop_usb_gadgets
	;;
	reconfigure)
	stop_usb_gadgets
	start_usb_gadgets $mass_storage_backend
	;;

        *)
	echo "Usage: $0 [start|stop|restart] [dev]"
	exit 1
        ;;
esac
