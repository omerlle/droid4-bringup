/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include <fcntl.h> //open
#include <unistd.h> //fork,exec
#include <regex>
#include <thread>
#include "misc_hardware_functions_and_class.h"

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
	std::string cmd("/usr/local/share/python/droid4_modem/software/main_new_sms.py ");
	cmd= cmd +arg;
	LOG_START << "cmd:" << cmd LOG_END;
	system(cmd.c_str());
}
void incoming_call(std::string *date, std::string call_number)
{
	droid4::modemDb db;
	std::string db_date=droid4::get_time(droid4::DB_DATE_TIME);
	*date=db_date;
	droid4::write_to_dev(droid4::LED_BLUE,"255");
	db.run(std::string("INSERT INTO voice_call_list (phone,date,status) VALUES('"+call_number+"','"+db_date+"',3);"));
        db.run(std::string("INSERT INTO notify_list(line,temp) VALUES ('--call:"+call_number+" ' || ( SELECT case WHEN ( SELECT phone_number FROM phone_book WHERE phone_number="+call_number+") not NULL then (SELECT case WHEN nickname not NULL then nickname WHEN last_name is NULL then first_name ELSE first_name || ' ' || last_name END FROM phone_book WHERE phone_number="+call_number+" ) ELSE '' END result) || ' "+db_date+"',1);"));
	droid4::write_to_dev(droid4::BLANK_SCREEN,"0");
	system("/usr/local/bin/droid4-notify.sh");
}
void start_conversation(std::string *date, std::string *call_number)
{
	droid4::modemDb db;
	if (!date->empty())
	{
		LOG_START << "UPDATE voice_call_list SET status=1 WHERE phone='"+*call_number+"' AND date='"+*date+"' LIMIT 1;" LOG_END;
		db.run("UPDATE voice_call_list SET status=1 WHERE id = (SELECT id FROM voice_call_list WHERE phone='"+*call_number+"' AND date='"+*date+"' LIMIT 1);");
		*date="";
	}
	*call_number="";
        db.run("DELETE FROM notify_list WHERE temp=1;");
	droid4::write_to_dev(droid4::BLANK_SCREEN,"1");
}
void hangup(std::string *date, std::string *call_number)
{
	droid4::write_to_dev(droid4::LED_BLUE,"0");
	if(*date != "" || *call_number!="")
	{
		*date="";
		*call_number="";
		droid4::write_to_dev(droid4::LED_RED,"255");
		droid4::modemDb().run("UPDATE notify_list SET temp=0 WHERE temp=1;");
		droid4::write_to_dev(droid4::BLANK_SCREEN,"1");
	}
}
void dials()
{
	droid4::write_to_dev(droid4::LED_BLUE,"255");
	droid4::modemDb().run("UPDATE voice_call_list SET temp = null WHERE temp=1;");
}
void call_waiting(const std::string &call_number)
{
        droid4::modemDb db;
	std::string db_date=droid4::get_time(droid4::DB_DATE_TIME);
        db.run(std::string("INSERT INTO voice_call_list (phone,date,status) VALUES('"+call_number+"','"+db_date+"',3);"));
	std::string line("'--:waiting"+call_number+" ' || ( SELECT case WHEN ( SELECT phone_number FROM phone_book WHERE phone_number="+call_number+") not NULL then (SELECT case WHEN nickname not NULL then nickname WHEN last_name is NULL then first_name ELSE first_name || ' ' || last_name END FROM phone_book WHERE phone_number="+call_number+" ) ELSE '' END result) || ' "+db_date+"'");
        db.run(std::string("INSERT INTO notify_list(line) VALUES ("+line+");"));
	db.run(std::string("INSERT INTO notify_list (line,temp) VALUES ("+line+",1);"));
	droid4::write_to_dev(droid4::BLANK_SCREEN,"0");
        system("/usr/local/bin/droid4-notify.sh");
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
	static const std::regex incoming_call_numder_pattern("^.*=\"([0-9]+)\".*");
	static bool is_ring=false;
	static std::string current_call_number="";
	static std::string current_call_time="";
	std::smatch results;
	if (!std::regex_match (event,results,modem_prefix_pattern))
	{
		LOG_START << " error bad prefix U####:" << event LOG_END;
		return;
	}
	event=results[1];
	bool is_incoming_call=(event.find("~+CLIP=")== 0);
	if(is_incoming_call || (event.find("~+CCWA=") == 0))
	{
		LOG_START << event LOG_END;
		std::string call_number;
		if (std::regex_match (event,results,incoming_call_numder_pattern))
		{
			call_number=results[1];
		}else call_number="privileged";
		if (is_incoming_call)
		{
			LOG_START << current_call_time <<  call_number LOG_END;
			std::thread(incoming_call,&current_call_time,call_number).detach();
			current_call_number=call_number;
		}else /*call_waiting*/
		{
			std::thread(call_waiting,call_number).detach();
			current_call_number="call_waiting";
		}
	}else if(event.find("~+CIEV=") == 0)
	{
		if(event=="~+CIEV=1,4,0")
		{
			is_ring=true;
			std::thread(ring,&is_ring,1500).detach();
			LOG_START << "INCOMING_CALL" << event LOG_END;
		}else if(event=="~+CIEV=1,2,0")
		{
			std::thread(start_conversation,&current_call_time,&current_call_number).detach();
			LOG_START << "START_CONVERSATION" << event LOG_END;
			is_ring=false;
		}else if (event=="~+CIEV=1,1,0")
		{
			std::thread(dials).detach();
			LOG_START << "DIALS" << event LOG_END;
		}else if (event=="~+CIEV=1,0,0" || event=="~+CIEV=1,0,2" || event=="~+CIEV=1,0,4")
		{
			std::thread(hangup,&current_call_time,&current_call_number).detach();
			LOG_START << "HANGUP" << event LOG_END;
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
