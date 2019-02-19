function backlight {
# Check for input file on command-line.
	ARGS=2
	E_BADARGS=85
	E_NOFILE=86
	if [ $# -ne "$ARGS" ]
	# Correct number of arguments passed to script?
	then
		echo "Usage: `basename $0` device stat"
		echo "Parameters:"
		echo "- device:   device name(lcd/keyboard)"
		echo "- stat:   the stat of the device(on/off)"

		return $E_BADARGS
	fi
	local device=$1
	local stat=$2
	if [ "$device" == "lcd" ] ;then
		file="/sys/class/backlight/lcd/brightness"
		name="backlight:lcd"
	elif [ "$device" == "keyboard" ] ;then
		file="/sys/class/leds/kbd_backlight/brightness"
		name="leds:kbd_backlight"
	else
		echo "bad device(\"$1\") must be one of the option lcd or keyboard."
		return $E_BADARGS
	fi
	if [ "$stat" != "on" -a "$stat" != "off" ] ;then
        	echo "stat is not on or off."
	         return $E_BADARGS
	fi
##################################################### 
	if [ "$stat" == "on" ] ;then
		/lib/systemd/systemd-backlight load $name
	else
		if [ ! -f "$file" ] ;then
			echo "error file \"$file\" does not exist."
			 return $E_NOFILE
		fi
		/lib/systemd/systemd-backlight save $name
		echo 0 > $file
	fi
}
