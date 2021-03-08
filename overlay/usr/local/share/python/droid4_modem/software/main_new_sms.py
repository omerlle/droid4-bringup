#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import logging
import select
import os
import sys

import utils.date_helper as date_helper
import droid4_modem.software.helpers as helpers
import droid4_modem.software.sms_parser as pdu
import droid4_modem.config.app_config as config
import hardware.led_handler as leds
import datetime
import utils.sqlite_helper

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

if __name__ == '__main__':
	logging.basicConfig(filename=config.LOG_PATH_PREFIX+date_helper.date_to_string(format=date_helper.DateStringFormat.FILENAME)+'_modem_app.log',level=logging.DEBUG,format='[%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d]:%(asctime)s|%(message)s',)
	logging.getLogger('droid4.new_sms')
	if len(sys.argv) != 2:
		logging.error("bad cmdline arguments: "+str(sys.argv))
		exit(2)
	line=sys.argv[1]
	db=utils.sqlite_helper.SqliteHelper(config.DATABASE_FILENAME,False)
	inform_msg=None
	sms = pdu.PDUReceive(line)
	adv=str(sms.reference_number)+","+str(sms.sequence_part_number)+"/"+str(sms.total_parts_number) if sms.total_parts_number > 1 else "1/1"
	logging.debug(sms.tpdu+","+sms.SenderPhoneNumber+","+sms.ServiceCenterDateStamp+","+sms.msg+","+adv)
	inform_msg=None
	if sms.total_parts_number == 1:
		msg_id=-1
	else:
		msg_ids=db.get_list_sql("select id from messages where reference_number="+str(sms.reference_number)+" and total_parts_number="+str(sms.total_parts_number)+" and phone_number='"+ sms.SenderPhoneNumber+"' and complete='n';") # (complete='n'?)'
		if len(msg_ids) == 0 : msg_id=-1
		elif len(msg_ids) == 1: msg_id=msg_ids[0]
		elif len(msg_ids) > 1:msg_id=self.db.get_value_sql("SELECT id,max(date) from pdu where msg_id in ("+",".join(msg_ids)+")")
		msg_id=int(msg_id)
	if msg_id == -1:
		inform_msg=True if sms.total_parts_number == 1 else False
		db_name=helpers.get_name_by_phone(db,sms.SenderPhoneNumber)
		if sms.total_parts_number == 1:
			msg_id=db.insert_row_and_get_id('INSERT INTO messages (msg, phone_number, date, phone_book_nickname) VALUES (?,?,?,?)',(sms.msg,sms.SenderPhoneNumber,sms.ServiceCenterDateStamp,db_name))
		else:
			msg_id=db.insert_row_and_get_id("INSERT INTO messages (phone_number, date, complete, total_parts_number, reference_number, phone_book_nickname) VALUES (?,?,'n',?,?,?)",(sms.SenderPhoneNumber,sms.ServiceCenterDateStamp,sms.total_parts_number, sms.reference_number, db_name))
	if sms.total_parts_number == 1:
		msg=sms.msg
		sms_date=sms.ServiceCenterDateStamp
		db.run_sql('INSERT INTO pdus (pdu, date, msg_id) VALUES (?,?,?)',(sms.tpdu,sms.ServiceCenterDateStamp, msg_id))
	else:
		db.run_sql('INSERT INTO pdus (pdu, date, msg_id, sequence_part_number, tmp_msg) VALUES (?,?,?,?,?)',(sms.tpdu, sms.ServiceCenterDateStamp, msg_id, sms.sequence_part_number, sms.msg))
	if inform_msg==None and sms.total_parts_number == int(db.get_value_sql("SELECT count(id) from pdus where msg_id="+str(msg_id)+";")):
		inform_msg=True
		msg="".join(db.get_list_sql("SELECT tmp_msg from pdus WHERE msg_id=" + str(msg_id) +" ORDER BY sequence_part_number"))
		logging.debug(msg)
		db.run_sql("UPDATE messages SET msg = ? ,complete='y',status=1 WHERE id = ? ;",(msg,msg_id))
		db.run_sql("UPDATE pdus SET tmp_msg = Null WHERE msg_id = " + str(msg_id) +";")
		sms_date, db_name=db.get_data_sql('SELECT date, phone_book_nickname FROM messages WHERE id = ' + str(msg_id) +";")[0]
	inform_msg=[msg,sms_date, sms.SenderPhoneNumber,db_name] if inform_msg==True else None
	if inform_msg:
		if config.LEDS_ENABLE: leds.Leds().set_leds(leds.LedName.RED,leds.LedAction.SET,255)
		message,date,phone,nickname=inform_msg
		if not nickname: nickname=""
		logging.warning("GET_SMS:"+phone+"("+nickname+")"+message)
		if config.NOTIFY_EVENTS:
				lines=["--sms:"+nickname+" "+phone+" "+date]
				lines.extend(message.rstrip().split("\n"))
				db.run_sql("INSERT INTO notify_list (line) VALUES (?)",list(map(lambda el:[el], lines)),True)
