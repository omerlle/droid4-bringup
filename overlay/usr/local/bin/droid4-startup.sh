#!/bin/sh
mac=""
UART_IDLE_MS=3000
#
# Note that this does not consider the calibration data right now
#
read_mac() {
        tmp=$(busybox mktemp -d)
	if [ "${tmp}" = "" ]; then
		echo "Could not make a tmp directory"
		return
	fi

        if ! mount -o ro /dev/mmcblk1p7 /${tmp}; then
                echo "Could not mount pds"
                return
        fi

        if [ ! -f ${tmp}/wifi/nvs_map.bin ]; then
                echo "Could not find nvs_map.bin"
                umount ${tmp}
                return
        fi

        bytes=$(hexdump -C ${tmp}/wifi/nvs_map.bin | head -n1 | \
                        cut -d' ' -f6,7,8,9,14,15)

        for byte in ${bytes}; do
                if [ "${mac}" == "" ]; then
                        mac=${byte}
                else
                        mac=${byte}:${mac}
                fi
        done

        echo "Read WLAN MAC from nvs_map.bin: ${mac}"

        umount ${tmp}
}
set_alsa() {
	#set alsamixer for voice call
	amixer set "Speaker Right" "Voice"
	amixer set "Call Noise Cancellation" unmute
	amixer set "Call" 100%
	amixer set "Mic2" 40%
	amixer set "Left" "Mic 2"
	amixer set "Voice" 55%
	amixer set "Mic2" 100%
	amixer set "Call Output" Speakerphone
}
start_wlan(){
	read_mac
        if [ "${mac}" != "" ]; then
                ifconfig wlan0 down
                ifconfig wlan0 hw ether ${mac}
        else
                echo "Could not read WLAN MAC"
                return 1
        fi
}
case $1 in
	start)
		for process in $processes ; do
			#wlan		
			if [ "$process" == "wlan" ] ; then
				start_wlan
			fi
			#alsa
			if [ "$process" == "alsa" ] ; then
				set_alsa
			fi
		done
	;;
	*)
        	echo "Usage: $0 [start]"
        	exit 1
        ;;
esac
