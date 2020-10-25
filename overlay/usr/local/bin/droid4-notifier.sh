#!/bin/bash
trap 'clean_msg' 2
clean_msg()
{
	echo -n "" > /tmp/notify_list
	list=""
	chvt 1
}
add_to_list()
{
	list="$1"$'\n'"$list"
}
make_msg()
{
	if [ "${action::7}" != "action:" ] ; then
		echo "bad syntax, no 'action:'($action)" >&2
		return
	fi
	case ${action:7} in
		got_new_sms)
			if [ "${lines::9}" != "details: " ] ; then
				echo "bad syntax, no 'details:'($lines)" >&2
				return
			fi
			add_to_list "${lines:9}-----$(cut -d ' ' -f4 <<< ${lines%%$'\n'*})-----"$'\n'
			msg=$list
		;;
		got_call)
			if [ "${lines::9}" != "details: " ] ; then
				echo "bad syntax, no 'details:'($lines)" >&2
				return
			fi
			pending="${lines:9}$(cut -d " " -f 4 <<< ${lines%$'\n'})"$'\n'
			msg="\n\n\n\n\n\n$pending...call"
		;;
		call_status)
			if [ "${lines::9}" != "details: " ] ; then
                                echo "bad syntax, no 'details:'($lines)" >&2
                                return                                      
                        fi
			local status=$(cut -d " " -f 4 <<< ${lines%$'\n'})
			if [ "$status" -eq "3" -a -n "$pending" ] ; then
				add_to_list "$pending"
			fi
			pending=""	
			msg=$list
		;;
		*)
			echo "bad action($action)" >&2
			return
		;;
	esac
}
print_msg()
{
	echo "XXX"
	echo "0"
	echo "$1";
	echo "XXX"
}
if [ ! -p /root/modem_notifications ] ; then
	mkfifo /root/modem_notifications
fi
cat /root/modem_notifications >> /tmp/notify_list &
while :
do
	tail -f /tmp/notify_list | 
		while :
		do 
			read line
			if [ "${line::6}" != "lines:" ] ; then
				echo "bad state($line)" >&2
				continue
			fi 
			num_lines=${line:6}
			if [ "$num_lines" -ge "1" ] ; then :
			else 
				echo "bad num lines($line)" >&2
				continue
			fi
			i=1
			read action
			lines=""
			while [ "$i" -lt "$num_lines" ] ; do
				((i++))
				read line
				lines="$lines$line"$'\n'
			done
			msg=""
			make_msg
			if [ ! -z "$msg" ] ;then
				print_msg "$msg"
				chvt 6
			fi
		done | dialog --gauge "" 30 60 0
done
