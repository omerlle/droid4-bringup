/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include <string>
#include <sstream>
#include <fstream>
#define LOG_START do {time_t t(time(NULL)); std::ostringstream msg;msg << ctime(&t) << "[INFO]:" << __FILE__ << " " << __LINE__ << " " << __func__ << ":"
#define LOG_END << std::endl; printf("%s", msg.str().c_str());/*fflush(stdout);*/} while (0);
namespace droid4
{
	enum dev_names:int {FIRST_POLL=0,BUTTONS_KEYBOARD_VOLUMEUP=FIRST_POLL,BUTTONS_POWER,BUTTONS_VOLUMEDOWN_SLIDE,BUTTONS_LAST=BUTTONS_VOLUMEDOWN_SLIDE,MODEM_CONTROL, INCOMING_SMS, BLANK_SCREEN, LAST_POLL=BLANK_SCREEN,EVENT_VIBRATOR, UNKNOWN_DEVICE_NAME,LAST_DEVICE_NAME=UNKNOWN_DEVICE_NAME};
	static const char *dev_filenames[LAST_DEVICE_NAME]={"/dev/input/by-path/platform-4a31c000.keypad-event","/dev/input/by-path/platform-48098000.spi-platform-cpcap-pwrbutton.0-event","/dev/input/by-path/platform-gpio_keys-event","/dev/gsmtty1","/dev/gsmtty9","/sys/devices/platform/omapdrm.0/graphics/fb0/blank","/dev/input/by-path/platform-vibrator-event"};
	inline void write_to_dev(dev_names dev,const std::string &pattern){std::ofstream(dev_filenames[dev]) << pattern;};
	void buttons_read_event(int fd);
	void init_modem();
	void modem_handle_event(int fd,dev_names device);
	class vibrator{
			bool open_fd();
		public:
			vibrator():_fd(-1),_id(-1),_len(1500){};
			bool set_vibrate_effect(int);
			bool vibrate(int=-1);
			~vibrator();
		private:
			int _fd,_id,_len;
	};
}
