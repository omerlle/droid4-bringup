/*
 *  License: LGPL 2.1
 *  Copyright (C) 2020  omer levin <omerlle@gmail.com>
*/

#include <sqlite3.h>
#include "misc_hardware_functions_and_class.h"
const char *droid4::modemDb::_db_path="/root/.droid4/modem/dynamic_data.db";
bool droid4::modemDb::open_db()
{
	int fail = sqlite3_open(_db_path, &_db);
	if (fail) {
                LOG_START << "Error open DB " << sqlite3_errmsg(_db) LOG_END;
                return false;
	}
	return true;
}
bool droid4::modemDb::run(const std::string &sql)
{
        if (!_db && !open_db()) return false;
	char* messaggeError;
	int fail = sqlite3_exec(_db, sql.c_str(), NULL, 0, &messaggeError);
	if (fail != SQLITE_OK)
	{
		LOG_START << "Error run Sql:" << messaggeError LOG_END;
		sqlite3_free(messaggeError);
		return false;
	}
	return true;
}
void droid4::modemDb::close_db()
{
	if (_db)
	{
		sqlite3_close(_db);
	}
}
droid4::modemDb::~modemDb()
{
        close_db();
}
