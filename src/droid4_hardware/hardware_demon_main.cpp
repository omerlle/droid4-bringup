/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include "misc_hardware_functions_and_class.h"
#include <unistd.h>
#include <fcntl.h> //O_RDONLY
#include <poll.h> // pollfd
int main(int argc, char** argv)
{
	const int timeout=60*1000*30;//-1;
	struct pollfd poll_fd[droid4::LAST_POLL];
	sleep(4);
	LOG_START << "run..." LOG_END;
        for (int i=droid4::FIRST_POLL;i< droid4::LAST_POLL;i++)
        {
                poll_fd[i].events = POLLIN;
                poll_fd[i].fd = open(droid4::dev_filenames[i],O_RDONLY|O_NONBLOCK);
                if (poll_fd[i].fd<=0)
                {
                        system("echo 'init fail, exit...' > /dev/tty1");
                        exit(-1);
                }
        }
	LOG_START << "MODEM_CONTROL fd="<< poll_fd[droid4::MODEM_CONTROL].fd << " INCOMING_SMS fd="<< poll_fd[droid4::INCOMING_SMS].fd  LOG_END;
	droid4::init_modem();
	while (true)
	{
		int ret = poll(poll_fd, droid4::LAST_POLL, timeout);
	        if (ret > 0)
		{
	                for (int i=droid4::FIRST_POLL; i<droid4::LAST_POLL; i++)
        	        {
				if (poll_fd[i].revents != 0)
				{
					if(i>=droid4::FIRST_POLL && i<=droid4::BUTTONS_LAST)
					{
						droid4::buttons_read_event(poll_fd[i].fd);
					}else if (i == droid4::MODEM_CONTROL || i == droid4::INCOMING_SMS)
					{
						droid4::modem_handle_event(poll_fd[i].fd, static_cast<droid4::dev_names>(i));
					}else
					{
						LOG_START << "error bad device:" << i LOG_END
					}
                                }
			}
		}else
		{
			system("/etc/init.d/droid4-pm status >> /root/.droid4/power");
		}
        }
}
