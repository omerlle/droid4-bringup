alias op="emacs --no-splash -l /usr/local/share/emacs/client_app.elc"
alias oc="/usr/local/share/python/droid4_modem/software/main_modem_cli.py"
alias ok="echo 255 > /sys/class/leds/lm3532\:\:kbd_backlight/brightness"
alias okf="echo 0 > /sys/class/leds/lm3532\:\:kbd_backlight/brightness"
alias owh='printf "U0000AT+CHLD=0\r" > /dev/gsmtty1'
alias owa='printf "U0000AT+CHLD=2\r" > /dev/gsmtty1'
alias on="sqlite3 /root/.droid4/modem/dynamic_data.db 'DELETE FROM notify_list;'"
alias os="sqlite3 /root/.droid4/modem/dynamic_data.db \"select pdus.id, pdus.date, sequence_part_number, phone_number, phone_book_nickname, tmp_msg FROM pdus LEFT JOIN messages ON messages.id = pdus.msg_id where messages.status=1 and tmp_msg!=''\""
