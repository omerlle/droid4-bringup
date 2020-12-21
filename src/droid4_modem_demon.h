/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#ifndef SRC_DROIDMODEMDEMON_H_
#define SRC_DROIDMODEMDEMON_H_
#include <poll.h> // pollfd
#include <sstream> // stringstream
#include <time.h>       /* time_t, struct tm, time, localtime, asctime */

#define LOG_START do {time_t t(time(NULL)); std::ostringstream msg;msg << ctime(&t) << "[INFO]:" << __FILE__ << " " << __LINE__ << " " << __func__ << ":"
#define LOG_END << std::endl; printf("%s", msg.str().c_str());/*fflush(stdout);*/} while (0);

class DroidModemDemon {
	enum poll_names:int {MODEM_CONTROL=0,FIRST_POLL=MODEM_CONTROL, INCOMING_SMS, UNKNOWN_POLL, LAST_POLL=UNKNOWN_POLL};
	static std::string poll_filenames[LAST_POLL];
public:
	DroidModemDemon();
	bool pollModem();
private:
	void readFromFd(poll_names fd);
	bool getLine(int fd, std::string & line);
	bool readChar(int fd, char & c);
	struct pollfd _poll_fd[LAST_POLL];
	int _sms_length;
	bool _ring;
};

#endif
