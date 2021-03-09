#!/bin/sh
number="$1"
if [ ${#number} -ge 11 ] && [ ${#number} -le 12 ]; then
        case $number in
                ''|*[!0-9]*) echo bed number ;;
                *)
                        dtime=$(date +"%Y-%m-%d %T")
			sqlite3 /root/.droid4/modem/dynamic_data.db 'DELETE FROM voice_call_list WHERE temp=1;'
                        sqlite3 /root/.droid4/modem/dynamic_data.db "INSERT INTO voice_call_list (phone,date,status,temp) VALUES('$number','$dtime',2,1);"
                        printf "U0000ATD+${number},0\r" > /dev/gsmtty1
			echo "dial done"
                ;;
	esac
else
	echo bed number
fi
