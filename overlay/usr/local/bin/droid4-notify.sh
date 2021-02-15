#!/bin/sh
dtime=$(date +"%Y.%m.%d|%T")
clear >/dev/tty2
call=$(sqlite3 /root/.droid4/modem/dynamic_data.db 'SELECT line FROM notify_list WHERE temp==1;')
if [ -z "$call" ] ; then
    sqlite3 /root/.droid4/modem/dynamic_data.db 'SELECT line FROM (SELECT * FROM notify_list WHERE temp==0 ORDER BY id DESC LIMIT 18) ORDER BY id ASC;'| fold -w 60 | tail -n 18 >/dev/tty2
else
    echo $'\n\n\n\n\n\n'  > /dev/tty2
    echo $call > /dev/tty2
fi
echo  -n "***** $(echo ${dtime} | cut -d '|' -f 2) $(cat /sys/class/power_supply/battery/capacity_level) $(${dtime} | cut -d '|' -f 1) *****" > /dev/tty2 
chvt 2
echo "0" > /sys/class/leds/status-led:red/brightness
