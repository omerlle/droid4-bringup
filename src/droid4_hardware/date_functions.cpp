/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include "misc_hardware_functions_and_class.h"
#include <ctime>
#include <iomanip>	

std::string droid4::get_time(date_type type, time_t *sec_from_unix_epoch)
{
	if (sec_from_unix_epoch==NULL)
	{
		time(sec_from_unix_epoch);
	}
	std::stringstream date_stream;
	std::string format;
	switch(type)
	{
		case SHORT_DATE:
			format="%y.%m.%d";
		break;
		case DB_DATE_TIME:
			format="%Y-%m-%d %H:%M:%S";
		break;
		case LONG_DATE:
			format="%a %b %d %H:%M:%S %Y";
		break;
	}
	date_stream << std::put_time(localtime(sec_from_unix_epoch), format.c_str());
	return date_stream.str();
}

