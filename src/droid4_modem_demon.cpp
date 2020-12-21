/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/
#include <fcntl.h> //open
#include <unistd.h> //fork,exec,sleep
#include <regex>
#include <thread>
#include "droid4_modem_demon.h"

std::string DroidModemDemon::poll_filenames[LAST_POLL] = {"/dev/gsmtty1","/dev/gsmtty9"};
void vibrate(const std::string & arg)
{
	system((std::string("/usr/local/share/droid4/python3_packages/hardware/vibrator.py ") + arg).c_str());
}
void start_ring(bool *ring)
{
	while(*ring)
	{
		vibrate("300");
		usleep(30000);
	}
}
DroidModemDemon::DroidModemDemon()
{
	LOG_START << "start init" LOG_END;
	for (int i=FIRST_POLL;i< LAST_POLL;i++)
	{
		_poll_fd[i].events = POLLIN;
		_poll_fd[i].fd = open(poll_filenames[i].c_str(),O_RDONLY);
		if (_poll_fd[i].fd<=0)
		{
			system("echo 'init fail, exit...' > /dev/tty1");
			LOG_START << "init fail, exit..." LOG_END;
			exit(-1);
		}
		LOG_START << "new fd " << _poll_fd[i].fd << " of " << i LOG_END;
	}
	_sms_length=0;
	_ring=false;
	system("/usr/local/share/droid4/python3_packages/modem_wrapper/software/main.py -m on -s off");
	LOG_START << "finish init" LOG_END;
	system("echo 'init succeed' > /dev/tty1");
}
bool DroidModemDemon::pollModem()
{
	LOG_START << "start poll" LOG_END;
	int ret = poll(_poll_fd, LAST_POLL, -1);
	if (ret > 0) {
		for (int i=FIRST_POLL; i< LAST_POLL; i++)
		{
			if (_poll_fd[i].revents != 0) {
		  		readFromFd((poll_names)i);
			}
		}
	}else
	{
		LOG_START << "error poll timeout" LOG_END;
	}
	return false;
}
void modem_wrapper(const std::string & arg)
{
  std::string cmd("/usr/local/share/droid4/python3_packages/modem_wrapper/software/main.py system ");
      cmd= cmd +arg;
        LOG_START << "cmd:" << cmd LOG_END;
	system(cmd.c_str());
}
void DroidModemDemon::readFromFd(poll_names fd_name)
{
	static const std::regex modem_prefix_pattern("^U[0-9]{4}(.*)");
	static const std::regex awk_pattern("^U[0-9]{4}+GCNMA=OK.*");//t std::regex awk_pattern("^U[0-9]{4}+GCNMA=OK");
	static const std::regex incoming_sms_lenth_pattern("^U[0-9]{4}~+GCMT=([0-9]*).*");
	std::smatch results;
	std::string line;
	getLine(_poll_fd[fd_name].fd,line);
	LOG_START << "after getLine:" << line LOG_END;
	switch (fd_name)
	{
		case MODEM_CONTROL:
			if (!std::regex_match (line,results,modem_prefix_pattern))
			{
				LOG_START << " error bad prefix U####:" << line LOG_END;
			}
			line=results[1];
			if(line.find("~+CLIP=") == 0)
			{
				std::thread(modem_wrapper,std::string("'")+line+"'").detach();
			}else if(line.find("~+CIEV=") == 0)
			{
				if(line=="~+CIEV=1,4,0")
				{
       					std::thread(vibrate,"300").detach();
					LOG_START << "INCOMING_CALL" << line LOG_END;
					_ring=true;
					std::thread(start_ring,&_ring).detach();
				}else if(line=="~+CIEV=1,2,0")
				{
					LOG_START << "START_CONVERSATION" << line LOG_END;
					std::thread(modem_wrapper,"START_CONVERSATION").detach();
					_ring=false;
				}else if (line=="~+CIEV=1,1,0")
				{
					std::thread(modem_wrapper,"DIALS").detach();
					LOG_START << "DIALS" << line LOG_END;
				}else if (line=="~+CIEV=1,0,0" || line=="~+CIEV=1,0,2" || line=="~+CIEV=1,0,4")
				{
					std::thread(modem_wrapper,"HENGUP").detach();
					LOG_START << "HENGUP" << line LOG_END;
					_ring=false;
				}else if (line=="~+CIEV=1,7,0" || line=="~+CIEV=1,3,0")
				{
					LOG_START << "free" << line LOG_END;
				}else
				{
					LOG_START << " error bad ~+CIEV:" << line LOG_END;
				}
			}else if (line.find("~+RSSI=") == line.find("~+CREG=") == line.find("~+GSYST=") == std::string::npos && line != "~+WAKEUP" && line != "+CFUN:OK" && line != "+SCRN:OK" && line != "H:ERROR" && line != ":OK" && line != "D:OK" && line != "A:OK")
			{
				LOG_START << " error bad line:" << line LOG_END;
			}
		break;
		case INCOMING_SMS:
			if (std::regex_match (line,awk_pattern))
			{
				LOG_START << "get awk" << line LOG_END;	
			}else if (std::regex_match (line,results,incoming_sms_lenth_pattern))
			{
				std::stringstream(results[1]) >> _sms_length;
			}else if (line.find("0791")==0)// && _sms_length>0)
			{
				int fd(open(poll_filenames[INCOMING_SMS].c_str(),O_WRONLY| FD_CLOEXEC));
				if (fd<=0)
				{				
					LOG_START << "error bad fd " << fd LOG_END;
				}
				write(fd,"U0000AT+GCNMA=1\r",16);
				close(fd);
				if (line.length()!=_sms_length)
				{
					LOG_START << "error bad length(" << _sms_length << ")" LOG_END;
				}
				std::thread(modem_wrapper,line).detach();
				std::thread(vibrate,"150").detach();
				_sms_length=0;
			}else
			{
				LOG_START << "error get unknoun msg:" << line LOG_END;
			}
		break;
		default:
			LOG_START << "error bad fd_name " << fd_name LOG_END;
	}
}
bool DroidModemDemon::readChar(int fd, char & c)
{
	ssize_t ret = read(fd, &c, 1);
	if(ret != 1)
	{
		LOG_START << "error read fail " << strerror(errno) LOG_END
	}
	return ret==1;
}
bool DroidModemDemon::getLine(int fd, std::string & line)
{
	char c;
	readChar(fd, c);
	while(c != '\n')
	{
		line.push_back(c);
		readChar(fd, c);
	}
	return true;
}
