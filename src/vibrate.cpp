/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include "hardware_func.h"
#include <sys/types.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <fcntl.h>
#include <linux/input.h>
#include <stdio.h>

bool droid4::vibrator::open_fd()
{
	_fd = open(droid4::dev_filenames[droid4::EVENT_VIBRATOR], O_RDWR);       
        if (_fd == -1) {                                                            
                return false;                                                          
        }
	return true;
}
bool droid4::vibrator::set_vibrate_effect(int len =1500)
{
	if(_fd<0)
	{
		if (!open_fd()) return false;
	}
	struct ff_effect effect = {};                                               
        effect.type = FF_RUMBLE;                                                    
        effect.id = -1;                                                             
        effect.u.rumble.strong_magnitude = 0xFFFF;                                  
        effect.u.rumble.weak_magnitude = 0x0000;                                    
        effect.replay.length = len;                                                
        effect.replay.delay = 1000;
	int err = ioctl(_fd, EVIOCSFF, &effect);                                     
        if (err == -1)
	{                                                           
                return false;                                                            
        }
	_id = effect.id;
	_len=len;
	return true;
}
bool droid4::vibrator::vibrate(int len)
{
	if (_id<0 || (len>0 && len != _len))
	{
		bool ans = len > 0 ? set_vibrate_effect(len):set_vibrate_effect();
		if(!ans)
		{
			return false;
		}
	}
	struct input_event event = {};
        event.type = EV_FF;
	event.code = _id;
	event.value = 1;
	
	int err = write(_fd, (const void*) &event, sizeof(event));
	if (err == -1)
	{
		return false;
	}

	usleep(_len*1000);

	event.value = 0;

	err = write(_fd, (const void*) &event, sizeof(event));
	if (err == -1)
	{
		return false;
	}
	return true;
}
droid4::vibrator::~vibrator()
{
	close(_fd);
}
