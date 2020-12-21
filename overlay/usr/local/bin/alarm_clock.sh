#!/bin/sh

if [ "$1" == "mute" ] ; then
	amixer set "HiFi" 0%
	amixer set "Speaker Right" "Voice"
	exit 0
fi
d=$(($(date +%s --date=$1)-$(date +%s)))
if [ "$d" -le 0 ] ; then
	d=$(($d+(24*60*60)))
fi;
sleep $d
while [ true ] ; do 
	amixer set "Speaker Right" HiFi
	amixer set "HiFi" 100%
	aplay /usr/share/sounds/alsa/Front_Center.wav
	amixer set "HiFi" 0%
	amixer set "Speaker Right" "Voice"
	sleep 5
done
