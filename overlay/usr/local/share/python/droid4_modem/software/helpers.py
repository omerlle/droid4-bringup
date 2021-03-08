#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

from enum import Enum
import fcntl, os

import droid4_modem.config.app_config as config

class MessageStatus(Enum):
	UNREAD=1
	READ=2
	SEND=3
	SEND_FAIL=4
class CallsStatus(Enum):
	INCOMING_CALL=1
	DIALS=2
	MISS=3
class ConversationAction(Enum):
	INCOMING_CALL=1
	DIALS=2
	START_CONVERSATION=3
	HENGUP=4
class ModemError(Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg
class SmsLock:
	def __enter__(self):
		self.file = open(config.SMS_SEND_LOCK_FILENAME,'w')
		fcntl.lockf(self.file, fcntl.LOCK_EX)
	def __exit__(self, exc_type=None, exc_value=None, traceback=None):
		fcntl.lockf(self.file, fcntl.LOCK_UN)
		self.file.close()
#db helpers
def get_and_set_reference_number(db,phone,long_reference_number=True):#16-bit
	column_name='long_reference_number' if long_reference_number else 'short_reference_number'
	max_number=65535 if long_reference_number else 255
	db.run_sql("INSERT OR IGNORE INTO phones (phone) VALUES('"+phone+"');")
	reference_number=db.get_value_sql("SELECT "+column_name+" FROM phones WHERE phone ='" + phone +"';")
	db.run_sql("UPDATE phones SET "+column_name+" = '"+str(reference_number+1 if reference_number<max_number else 0)+"' WHERE phone='"+phone+"';")
	return reference_number
def get_name_by_phone(db,phone):
	data=db.get_data_sql("SELECT nickname,first_name,last_name FROM phone_book WHERE phone_number='"+phone+"';")
	if data:
		nickname,first_name,last_name=data[0]
		name=nickname if nickname else first_name + " " + str(last_name)
	else:
		name=""
	return name
	return nickname if nickname else first_name + " " + str(last_name)
