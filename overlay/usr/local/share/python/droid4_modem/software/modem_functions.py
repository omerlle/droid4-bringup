#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import logging
import select
import subprocess
import os

import utils.date_helper as date_helper
import droid4_modem.software.helpers as helpers
import droid4_modem.software.sms_parser as pdu
import droid4_modem.config.app_config as config
import hardware.led_handler as leds
import datetime
import utils.sqlite_helper

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

class ModemWrapper():
	def __init__(self):
		self.db=utils.sqlite_helper.SqliteHelper(config.DATABASE_FILENAME,False)
	def write_to_modem(self,cmd):
		logging.debug("cmd:"+cmd)
		with open(config.MODEM_DEV, "w") as dev:
			dev.write("U0000"+cmd+"\r")
	def check_output(self,timeout,modem_read):
		poll=select.poll()
		poll.register(modem_read.fileno(),select.POLLIN)
		events=poll.poll(timeout)
		if not events:logging.error('timeout('+str(timeout)+')')
		for fd,event in events:
			if fd != modem_read.fileno():raise helpers.ModemError("bad fd:"+fd)
			if event != select.POLLIN:raise helpers.ModemError("bad event:"+str(event))
			data = modem_read.readline()
			if "ERROR" in data:
				logging.error("Traceback Got ERROR: "+data)
			else:
				logging.debug("Got response: "+data)
				if data.startswith("U0000+GCMGS="):return int(data.split(',', 1)[0][12:])
		return None
	def send_sms(self,message, numbers=None, nicknames=None, ids=None):
		with helpers.SmsLock():
			phones=[]
			if nicknames:
				phones=self.db.get_data_sql("SELECT phone_number,nickname FROM phone_book WHERE nickname  in ('"+"','".join(nicknames)+"');")
			if ids:                                                                                                         
				phones.extend(self.db.get_data_sql("SELECT phone_number,nickname FROM phone_book WHERE id  in ("+",".join(map(str,ids))+");"))
			if numbers:phones.extend([[phone,''] for phone in numbers])
			logging.warning("SEND_SMS:("+",".join([phone+"("+str(nickname)+")" for phone,nickname in phones])+")"+message)
			modem_read = open(config.SMS_SEND_DEV,"r")
			self.check_output(0,modem_read)
			for phone,nickname in phones:
				pdus=pdu.PDUSend(phone,message,nickname,self.db)
				date=date_helper.date_to_string()
				logging.debug(pdus)
				msg_id=self.db.insert_row_and_get_id('INSERT INTO messages (msg, phone_number, date, phone_book_nickname,status,total_parts_number,complete) VALUES (?,?,?,?,?,?,?)',(message,phone,date,nickname,helpers.MessageStatus.SEND_FAIL.value,len(pdus.tpdus),'n'))
				succses=True
				pdu_num=1
				for line in pdus.tpdus:
					ans = None
					logging.debug(line)
					with open(config.SMS_SEND_DEV, "w") as dev:
						dev.write("U0000AT+GCMGS=\r")
						dev.write('U'+line + '\x1a\r')
					ans=self.check_output(-1,modem_read)#7sec
					if ans == None:succses=False
					else:self.db.run_sql('INSERT INTO pdus (pdu, date, msg_id, sequence_part_number, tmp_msg) VALUES (?,?,?,?,?)',(str(msg_id)+':'+str(pdu_num)+':'+line, date, msg_id, pdu_num, ans))
					pdu_num=pdu_num+1
				if succses:self.db.run_sql("UPDATE messages SET status = ? ,complete='y' WHERE id = ? ;",(helpers.MessageStatus.SEND.value,msg_id))
				else:
					logging.error('FAILED to send message')
			modem_read.close()
	def dials(self,privileged,is_nickname,phone):
		line_id=",1" if privileged else ",0"
		if is_nickname:phone = self.db.get_value_sql("SELECT phone_number FROM phone_book WHERE nickname='"+phone+"';")
		self.last_call = phone
		if self.db.get_value_sql("SELECT temp FROM voice_call_list WHERE temp=1;",True):
			logging.error('temp exist')
			self.db.run_sql("DELETE FROM voice_call_list WHERE temp=1;") 
		self.db.run_sql('INSERT INTO voice_call_list (phone,date,status,temp) VALUES(?,?,?,?)',(phone, date_helper.date_to_string(), helpers.CallsStatus.DIALS.value,1));
		logging.info('try to call:'+phone)
		self.write_to_modem("ATD+"+phone+line_id)
	def print_call_history(self, call_type=[], nicknames=[], phones=[], length=None):
		where=" WHERE " if call_type or nicknames or phones else " "
		if call_type:where=where+" status IN ("+ ",".join([str(t.value) for t in call_type])+")"
		where_nickname = "nickname in ('" + "','".join(nicknames)+"')" if nicknames else ""
		where_number = "phone in ('" + "','".join(phones)+"')" if phones else ""
		if nicknames and phones: where= where+" AND ( " + where_nickname + " OR " + where_number + ")"
		elif nicknames or phones: where= where + " AND " + where_nickname + where_number
		limit="LIMIT "+str(length) if length else ""
		for phone_number,phone_book_nickname, date, status in self.db.get_data_sql('SELECT phone, nickname, voice_call_list.date, voice_call_status.type FROM voice_call_list INNER JOIN voice_call_status ON voice_call_status.id = voice_call_list.status  LEFT JOIN phone_book ON phone_book.phone_number = voice_call_list.phone'+where+' ORDER BY voice_call_list.date DESC '+ limit +';'):
			if not phone_book_nickname:phone_book_nickname=""
			print(status+":"+phone_book_nickname+ "("+phone_number+")"+date)
	def sms_handle(self,mark=False,status=[],id=[],phone_book_nickname=[],phone_number=[], length=None, delete=False):
		if not self.db:self.connect_to_db()
		fileds='messages.id,phone_number,msg,phone_book_nickname, date, message_status.name'
		where=" WHERE complete='y'"
		if status:where=where+" AND status IN ("+ ",".join([str(s.value) for s in status])+")"
		if id : where=where+" AND messages.id IN (" + ",".join(map(str,id))+")"
		if phone_book_nickname or phone_number:
			where=where+ " AND ( " if phone_book_nickname and phone_number else where+" AND "
			if phone_book_nickname: where=where+"phone_book_nickname in ('" + "','".join(phone_book_nickname)+"')"
			if phone_book_nickname and phone_number:where=where+" OR "
			if phone_number: where=where+"phone_number in ('" + "','".join(phone_number)+"')"
			if phone_book_nickname and phone_number: where=where+")"
		limit="LIMIT "+str(length) if length else ""
		if delete:self.db.run_sql('DELETE FROM messages ' + where + limit + ';')
		else:
			for id,phone_number,msg,phone_book_nickname, date, status in self.db.get_data_sql('SELECT '+fileds+' FROM messages INNER JOIN message_status ON message_status.id = messages.status' + where +' ORDER BY date DESC '+  limit + ';'):
				print("("+str(id)+")"+phone_number+":"+str(phone_book_nickname)+":"+date+":"+status+":"+msg)
			if mark: self.db.run_sql('UPDATE messages SET status='+str(MessageStatus.READ.value) + where + ' AND status=' + str(MessageStatus.UNREAD.value) +  limit + ';')
	def show_phonebook(self, fileds, full=False,ids=[],phones=[],names=[],nicknames=[],last_names=[],subject=None,print_data=True):
		if not self.db:self.connect_to_db()
		where=""
		if ids or phones or nicknames or subject or names or last_names:
			sql_or=[]
			if ids:sql_or.append("id IN ("+",".join(map(str,ids))+")")
			if phones:
				phone_where="phone_number IN ("+",".join(phones)+")" if full else "phone_number LIKE '" + "%' OR phone_number LIKE '".join(phones)+"%'"  
				sql_or.append(phone_where)
			if nicknames:
				nickname_where="nickname IN ('"+"','".join(nicknames)+"')" if full else "nickname LIKE '" + "%' OR nickname LIKE '".join(nicknames)+"%'"
				sql_or.append(nickname_where)
			sql_and=[]
			if names:sql_and.append("first_name IN ('"+"','".join(names)+"')" if full else "first_name LIKE '" + "%' OR first_name LIKE '".join(names)+"%'")
			if last_names:sql_and.append("last_name IN ('"+"','".join(last_names)+"')" if full else "last_name LIKE '" + "%' OR last_name LIKE '".join(last_names)+"%'")
			if subject:sql_and.append("subject='"+subject+"'" if full else "subject LIKE '"+subject+"%'")
			if sql_and:sql_or.append("("+" AND ".join(sql_and)+")")
			where=" WHERE " + " OR ".join(sql_or)
		ans = self.db.get_data_sql('SELECT '+fileds+' FROM phone_book'+where+';')
		if print_data:
			for row in ans:
				print(":".join(map(str,row)))
		else: return None if not ans else ans[0][0]
	def edit_phonebook(self, id, phone=None, name=None, nickname=None, last_name=None, subject=None, description=None, update_date=False):
		if not self.db:self.connect_to_db()
		sql_set=[]
		if phone: sql_set.append("phone_number='"+phone+"'")
		if name: sql_set.append("first_name='"+name+"'")
		if nickname: sql_set.append("nickname='"+nickname+"'")
		if last_name: sql_set.append("last_name='"+last_name+"'")
		if subject: sql_set.append("subject='"+subject+"'")
		if description: sql_set.append("description='"+description+"'")
		if update_date:sql_set.append("date='"+date_helper.date_to_string()+"'")
		self.db.run_sql('UPDATE phone_book SET '+ ",".join(sql_set) + ' WHERE id=' + str(id) + ';')
	def update_phonebook_lists(self, update_phone_list, update_nickname_list):
		if not self.db:self.connect_to_db()
		if update_nickname_list:
			ans=self.db.get_data_sql('select phone_number,nickname from phone_book where nickname not null;')
			with open(config.NICKNAME_LIST_FILENAME, "w") as nickname_list:
				nickname_list.write("(setq nickname-list (make-hash-table :test 'equal))\n")
				for phone_number,nickname in ans:
					nickname_list.write('(puthash "'+nickname+"\" '(\""+nickname+'" "'+phone_number+'") nickname-list)\n')
			subprocess.run(["emacs", "-batch", "-f", "batch-byte-compile", config.NICKNAME_LIST_FILENAME])
		if update_phone_list:
			ans=self.db.get_data_sql('select subject text,first_name, last_name, nickname, id, description, date, phone_number from phone_book;')
			with open(config.PHONE_LIST_FILENAME, "w") as phone_list:
				for row in ans:
					phone_list.write('|'.join(map(str,row))+"\n")
