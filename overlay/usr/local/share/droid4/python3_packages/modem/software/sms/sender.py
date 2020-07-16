# -*- coding: utf-8 -*-
import logging
import threading
import traceback
import queue
import math
import select
from enum import Enum

import software.db_manager as sqlite_parser
import config.app_config as config

class MessageStatus(Enum):
        UNREAD=1
        READ=2
        SEND=3
        SEND_FAIL=4
class SmsSender:
	def __init__(self):
		self.db=None
		self.send_queue = queue.Queue()
		self.worker=threading.Thread(name="sender_worker",target=self.run)
	def start_thread(self):
		self.worker.setDaemon(True)
		self.worker.start()
	def stop_thread(self):
		self.send_queue.put(('stop',None))
	def send_msg(self,pdus,date):
		self.send_queue.put(('send',(pdus,date)))
	def check_output(self,modem_read,timeout):
		poll=select.poll()
		poll.register(modem_read.fileno(),select.POLLIN)
		events=poll.poll(timeout)
		for fd,event in events:
			if fd != modem_read.fileno():raise helpers.ModemError("bad fd:"+fd)
			if event != select.POLLIN:raise helpers.ModemError("bad event:"+str(event))
			data = modem_read.readline()
			#logging.debug("after read:"+data)
			if "ERROR" in data:
				logging.error("Traceback Got ERROR: "+data)
			else:
				logging.debug("Got response: "+data)
				if data.startswith("U0000+GCMGS="):return int(data.split(',', 1)[0][12:])
		return None
	def send(self,pdus,date):
		logging.debug(pdus)
		msg_id=self.db.insert_row_and_get_id('INSERT INTO messages (msg, phone_number, date, phone_book_nickname,status,total_parts_number,complete) VALUES (?,?,?,?,?,?,?)',(pdus.message,pdus.phone,date,pdus.nickname,MessageStatus.SEND_FAIL.value,len(pdus.tpdus),'n'))
		succses=True
		i=1
		for line in pdus.tpdus:
			logging.debug(line)
			modem_read = open(config.SMS_SEND_DEV,"r")
			self.check_output(modem_read,0)
			with open(config.SMS_SEND_DEV, "w") as dev:
				dev.write("U0000AT+GCMGS=\r")
			with open(config.SMS_SEND_DEV, "w") as dev:
				dev.write('U'+line + '\x1a\r')
			ans=self.check_output(modem_read,-1)
			if ans == None:succses=False
			else:self.db.run_sql('INSERT INTO pdus (pdu, date, msg_id, sequence_part_number, tmp_msg) VALUES (?,?,?,?,?)',(str(msg_id)+':'+str(i)+':'+line, date, msg_id, i, ans))
			i=i+1
			#self.check_output(modem_read,2)
		if succses:self.db.run_sql("UPDATE messages SET status = ? ,complete='y' WHERE id = ? ;",(MessageStatus.SEND.value,msg_id))	
	def run(self):
		self.db=sqlite_parser.sms_db()
		stop=False
		while not stop:
			cmd,args = self.send_queue.get()
			try:
				if cmd == 'stop':stop=True
				elif cmd == 'send':self.send(args[0],args[1])
				else :raise helpers.ModemError("bad cmd"+cmd)
			except Exception as e:
				logging.error(traceback.format_exc())
			self.send_queue.task_done()
	def __del__(self):
		pass
	def close(self):
		self.worker.join()
		logging.info("closed")
