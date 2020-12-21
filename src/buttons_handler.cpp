/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/
#include <sys/file.h>
#include <stdio.h>
#include <string.h>
#include <linux/input.h>
#include <unistd.h>
#include <poll.h> // pollfd
#include <fcntl.h>
#include <string>
#include <iostream>
#include <fstream>

int timeout=-1;
bool droid_en_keyboard=true;
std::ofstream droid_blank_screen,droid_modem;
enum dev_events{ev_first, ev_keyboard_volumeup=ev_first, ev_power, ev_volumedown_slide, ev_last};
void blank_screen()                                                                       
{                                                                                         
        droid_blank_screen.open ("/sys/devices/platform/omapdrm.0/graphics/fb0/blank");
        droid_blank_screen << "1";                                                     
        droid_blank_screen.close();                                                                                                                           
}
void handle_event(enum dev_events name, struct input_event &ev,int rd)
{
	if (ev.type == 1)
	{
		switch (ev.code)
		{
			case KEY_VOLUMEDOWN://volumedown released
			{
			        int fd(open("/dev/gsmtty1",O_WRONLY));
			        if (fd>0)
			        {
				     write(fd,"U0000ATH\r",9);
				     close(fd);
				}
                        }
			break;
			case KEY_VOLUMEUP://volumeup released
		        {  
			        int fd(open("/dev/gsmtty1",O_WRONLY));
			        if (fd>0)
			        {
				     write(fd,"U0000ATA\r",9);
				     close(fd);
				}
		        }
                        break;
                        case KEY_POWER://ok released                                                             
			        timeout=5000;//close_screen();
				system("/usr/local/share/droid4/python3_packages/modem_wrapper/software/main.py -n");
                        break;
                        case KEY_OK://power released                                                             
				droid_en_keyboard? system("loadkeys /usr/local/share/fonts/symbols"):system("loadkeys us");
				droid_en_keyboard=!droid_en_keyboard;
			break;
		}
	}else if (ev.type == 5 && ev.code == 10)
	{
		if (ev.value==0)//slide closed
		{
			    timeout=1000;
		}
	}
}
bool add_fd(int &fd, enum dev_events name)
{
        std::string filename="";
        switch (name)
        {
                case ev_keyboard_volumeup:
                        filename="/dev/input/by-path/platform-4a31c000.keypad-event";
                break;
                case ev_power:
                        filename="/dev/input/by-path/platform-48098000.spi-platform-cpcap-pwrbutton.0-event";
                break;
                case ev_volumedown_slide:
                        filename="/dev/input/by-path/platform-gpio_keys-event";
                break;
                default:
                        printf ("bad enum eve.\n");
                        fd=-1;
                        return false;
        }
        if ((fd = open(filename.c_str(),O_RDONLY|O_NONBLOCK)) == -1)
        {
                printf ("not a vaild device:%s.\n",filename.c_str());
                fd=-1;
                return false;
        }
        return true;
}
int main (int argc, char *argv[])
{
        struct input_event ev;
        int rd,ret;
        struct pollfd poll_fd[ev_last];
        for (int i=ev_first;i<ev_last;i++)
        {
                add_fd(poll_fd[i].fd, static_cast<enum dev_events>(i));
                if (poll_fd[i].fd != -1) poll_fd[i].events = POLLIN;
        }
        while (1){
                int ret = poll(poll_fd, ev_last,timeout);
                if (ret > 0) {
                        got_key=true;
			for (int i=ev_first;i<ev_last;i++)
                        {
                                if (poll_fd[i].revents != 0) {
					rd=1;
        	                        memset((void*)&ev, 0, sizeof(ev));
                	                while(rd>0)
                        	        {
                                	        rd = read (poll_fd[i].fd, (void*)&ev, sizeof(ev));
						if(rd>0 && ((ev.type==1 && ev.value==0) || ev.type==5))
       	                                        	handle_event(static_cast<enum dev_events>(i), ev, rd);
					}
                                }
			}
		}else
                {
			blank_screen();
			timeout=-1;
                }
        }
        return 0;
}
