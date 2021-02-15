/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include <fcntl.h> //open
#include <unistd.h> //fork,exec
#include <regex>
#include <thread>
#include "hardware_func.h"

void ring(bool *is_ring,int len)
{
	droid4::vibrator vib;
	vib.vibrate(len);
	while(*is_ring)
	{
		usleep(3000);
		vib.vibrate();
	}
}
void vibrate()
{
        droid4::vibrator().vibrate();
}
void droid4::init_modem()
{
	droid4::write_to_dev(droid4::MODEM_CONTROL,"U0000AT+CFUN=1\r");
	droid4::write_to_dev(droid4::MODEM_CONTROL,"U0000AT+SCRN=0\r");
}
void modem_wrapper(const std::string & arg)
{
	std::string cmd("/usr/local/share/droid4/python3_packages/modem_wrapper/software/main.py system ");
	cmd= cmd +arg;
	LOG_START << "cmd:" << cmd LOG_END;
	system(cmd.c_str());
}
bool readChar(int fd, char & c)
{
        ssize_t ret = read(fd, &c, 1);
        if(ret != 1)
        {
                LOG_START << "error read fail " << strerror(errno) LOG_END
        }

        return ret==1;
}
bool getLine(int fd, std::string & line)
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
void incoming_sms_event(std::string & event)
{
	static const std::regex awk_pattern("^U[0-9]{4}\\+GCNMA=OK.*");//t std::regex awk_pattern("^U[0-9]{4}+GCNMA=OK");
	static const std::regex incoming_sms_lenth_pattern("^U[0-9]{4}~\\+GCMT=([0-9]*).*");//t std::regex incoming_sms_lenth_pattern("^U[0-9]{4}~+GCMT=([0-9]*)");
	static int sms_length=0;
	std::smatch results;
	if (std::regex_match (event,awk_pattern))
	{
		LOG_START << "get awk:" << event LOG_END;
	}else if (std::regex_match (event,results,incoming_sms_lenth_pattern))
	{
		std::stringstream(results[1]) >> sms_length;
		LOG_START << "get sms len:" << results[1] LOG_END;
        }else if (event.find("0791")==0)// && sms_length>0)
        {
		droid4::write_to_dev(droid4::INCOMING_SMS,"U0000AT+GCNMA=1\r");
	        if (event.length()!=sms_length)
                {
            		LOG_START << "error bad length=" << event.length() <<"(" << sms_length << ")" LOG_END;
                }
                std::thread(modem_wrapper,event).detach();
                std::thread(vibrate).detach();
                sms_length=0;
        }else
        {
   	     LOG_START << "error get unknoun msg:" << event LOG_END;
        }
}
void modem_control_event(std::string & event)
{
	static const std::regex modem_prefix_pattern("^U[0-9]{4}(.*)");
	static bool is_ring=false;
	std::smatch results;
	if (!std::regex_match (event,results,modem_prefix_pattern))
	{
		LOG_START << " error bad prefix U####:" << event LOG_END;
	}
	event=results[1];
                        if(event.find("~+CLIP=") == 0)
                        {
                          std::thread(modem_wrapper,std::string("'")+event+"'").detach();
			}else if(event.find("~+CCWA=") == 0)
			{
				std::thread(modem_wrapper,std::string("'")+event+"'").detach();
                        }else if(event.find("~+CIEV=") == 0)
                        {
                                //"~+CIEV=1,4,0"-INCOMING_CALL
                                //"~+CIEV=1,2,0"-START_CONVERSATION
                                //"~+CIEV=1,1,0"-DAIL
                                //"~+CIEV=1,0,0"-HENGUP meybe my hendup
                                //"~+CIEV=1,0,4"-HENGUP meybe when i call and the other hengup
                                //"~+CIEV=1,3,0"- meybe free ring
	                        //"~+CIEV=1,7,0"- meybe free ring
                                //"~+CIEV=1,0,2"- meybe no anser
                                if(event=="~+CIEV=1,4,0")
                                {
                                        is_ring=true;
					std::thread(ring,&is_ring,1500).detach();
                                        LOG_START << "INCOMING_CALL" << event LOG_END;
                                }else if(event=="~+CIEV=1,2,0")
                                {
                                        std::thread(modem_wrapper,"START_CONVERSATION").detach();
                                        is_ring=false;
                                }else if (event=="~+CIEV=1,1,0")
                                {
                                       std::thread(modem_wrapper,"DIALS").detach();
                                }else if (event=="~+CIEV=1,0,0" || event=="~+CIEV=1,0,2" || event=="~+CIEV=1,0,4")
                                {
                                        std::thread(modem_wrapper,"HENGUP").detach();
                                        is_ring=false;
                                }else if (event=="~+CIEV=1,7,0" || event=="~+CIEV=1,3,0")
                                {
                                        LOG_START << "free" << event LOG_END;
                                }else
                                {
                                        LOG_START << " error bad ~+CIEV:" << event LOG_END;
                                }
                        }else if (event.find("+CFUN:OK")==0)
			{
				system("echo 'init succeed' > /dev/tty1");
			}else if (event.find("~+RSSI=") == event.find("~+CREG=") == event.find("~+GSYST=") == std::string::npos && event != "~+WAKEUP" && event != "+SCRN:OK" && event != "H:ERROR" && event != ":OK" && event != "D:OK" && event != "A:OK")
                        {
                                LOG_START << " error bad line:" << event LOG_END;
                        }
}
void droid4::modem_handle_event(int fd, dev_names device)
{
	std::string line;
	LOG_START << "after" LOG_END;
	getLine(fd,line);
	LOG_START << "after getLine:" << line LOG_END;
	if(device==droid4::MODEM_CONTROL)
	{
		modem_control_event(line);
	}else if (device==droid4::INCOMING_SMS)
	{
		incoming_sms_event(line);
	}else
	{
		LOG_START << "error bad device:"<< device LOG_END;
	}
}
