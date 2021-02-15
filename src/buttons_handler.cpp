/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include <sys/file.h>
#include <stdio.h>
#include <linux/input.h>
#include <unistd.h>
#include <fcntl.h>
#include <iostream>
#include <fstream>
#include <thread>
#include <cstring> //memset
#include "hardware_func.h"

void blank_screen(int delay,bool *close_screen)                                                                       
{
	*close_screen=true;
	if (delay>0)
	{
		sleep(delay);
	}
	if (*close_screen)
	{
		droid4::write_to_dev(droid4::BLANK_SCREEN,"1");
	}
}
void peek(bool *close_screen)
{
	system("/usr/local/bin/droid4-notify.sh");
	blank_screen(10,close_screen);
}
void buttons_handle_event(struct input_event &ev)
{
	static bool close_screen=false;
	close_screen=false;
	if (ev.type == 1)
	{
		switch (ev.code)
		{
			case KEY_VOLUMEDOWN://volumedown released
				droid4::write_to_dev(droid4::MODEM_CONTROL,"U0000ATH\r");
				std::thread(blank_screen,1,&close_screen).detach();
			break;
			case KEY_VOLUMEUP://volumeup released
				droid4::write_to_dev(droid4::MODEM_CONTROL,"U0000ATA\r");
				std::thread(blank_screen,1,&close_screen).detach();
                        break;
                        case KEY_POWER://power released
				std::thread(peek,&close_screen).detach();
                        break;
                        case KEY_OK://ok released
			{
				static bool droid_en_keyboard=true;                                                             
				droid_en_keyboard? system("loadkeys /usr/local/share/fonts/symbols"):system("loadkeys us");
				droid_en_keyboard=!droid_en_keyboard;
			}
			break;
		}
	}else if (ev.type == 5 && ev.code == 10)//slide slide closed. ev.value==1 for slide opened
	{
		std::thread(blank_screen,1,&close_screen).detach();
	} 
}
void droid4::buttons_read_event(int fd)
{
	struct input_event ev;
	int rd=1;
  	memset((void*)&ev, 0, sizeof(ev));
        while(rd>0)
	{
		rd = read (fd, (void*)&ev, sizeof(ev));
		if(rd>0 && ev.value==0 && (ev.type==1 || ev.type==5))//slide opened:ev.value==1, ev.type == 5, ev.code == 10
       	        {        
			buttons_handle_event(ev);
		}
	}
}
