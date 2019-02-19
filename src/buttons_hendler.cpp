#include <sys/file.h>
#include <string.h>
#include <linux/input.h>
#include <unistd.h>
#include <poll.h> // pollfd
#include <fstream>


void powerOffRelease()//, int value)
{
	std::string brightness;
	std::fstream brightness_f("/sys/class/backlight/lcd/brightness");
	if (!brightness_f.is_open())
	{
		printf ("cann't open device.\n");
	}else
	{
		brightness_f >> brightness;
		if (brightness != "0")
		{
			system("/lib/systemd/systemd-backlight save backlight:lcd;/lib/systemd/systemd-backlight save leds:kbd_backlight;echo 0 > /sys/class/leds/kbd_backlight/brightness");
			brightness_f << "0";
		}else
		{
			system("/lib/systemd/systemd-backlight load backlight:lcd;/lib/systemd/systemd-backlight load leds:kbd_backlight");
		}
	}
}
void readEvent(int fd)
{
	struct input_event ev;
	memset((void*)&ev, 0, sizeof(ev));
	int size = read (fd, (void*)&ev, sizeof(ev));
	if (size <= 0){
		printf ("rd: %d\n", size);
                sleep(1);
        }
	if(size>0 && ev.value==0 && ev.type==1){
		//printf("type: %d, code: %d, value: %d, rd: %d\n", ev.type, ev.code, ev.value, size);
		switch(ev.code)
		{
			case 114:
				printf ("volume down.\n");
			break;
			case 115:
				printf ("volume up.\n");
			break;
			case 116:
				printf ("poweroff.\n");
				powerOffRelease();
			break;
		}
	}
}
int main (int argc, char *argv[])
{
	int ret;
       struct pollfd poll_fd[4];
	for (int i=0; i<4;i++)
	{
		poll_fd[i].events=POLLIN;
		std::string filename="/dev/input/event";
		if ((poll_fd[i].fd = open((filename+std::to_string(i)).c_str(),O_RDONLY|O_NONBLOCK)) == -1)//FD_CLOEXEC;
		{
                	printf ("not a vaild device.\n");
        	}
	}
        while (1){
                ret = poll(poll_fd, 4,-1);
		if (ret > 0) {
		/* An event on one of the fds has occurred. */
			bool is_revents=false;
			for (int i=0; i<4;i++)
			{
				if (poll_fd[i].revents != 0) 
				{
					readEvent(poll_fd[i].fd);
					is_revents=true;
				}
			}
			if (!is_revents)
			{
				printf ("no event.\n");
			}
                }else
		{
			printf ("timeout.\n");
		}
        }
        return 0;
}
