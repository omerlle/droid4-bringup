#!/bin/sh
echo "wait..."
connected=false 
qmicli -d /dev/cdc-wdm0 --wds-follow-network --wds-start-network=apn=internet.t-mobile.cz | while read line ; do 
	if [ "$line" == "[/dev/cdc-wdm0] Network started" ] ; then
		echo "Network started"
		ifconfig wwan0 up
		sleep 1
		dhclient wwan0
	fi
	if [ "$connected" = false ] && [ "$line" == "[/dev/cdc-wdm0] Connection status: 'connected'" ] ; then 
#		ifconfig wwan0 up
#		dhclient wwan0
		echo "connected"
		connected=true
	fi
#	echo "tmp$line"
done
pkill dhclient
ifconfig wwan0 down
