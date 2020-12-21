/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include "droid4_modem_demon.h"
#include <unistd.h>
int main(int argc, char** argv)
{
	sleep(4);
	LOG_START << "run..." LOG_END;
	DroidModemDemon droid4_modem;
	while (true)
	{
		droid4_modem.pollModem();
	}
}
