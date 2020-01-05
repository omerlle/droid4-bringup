# -*- coding: utf-8 -*-
import config.app_config as config
import software.db_manager as sqlite_parser
import software.sms.receiver as sms_receiver
import software.sms.sender as sms_sender
import software.mamagers_client as clients
from software.sms import pdu
import string
import traceback
import logging
import threading
import utils.date_helper
import math
import hardware.led_handler as leds_handler
import hardware.vibrator as vibrator
class SmsManager:
	def __init__(self):
		self.db=None
		self.sms_queue=clients.managers_queues[clients.managers.sms.value]
		self.pipe_client = clients.PipeClient()
		self.worker=threading.Thread(name="sms_manager_worker",target=self.run)
		self.receiver = sms_receiver.SmsReceiver()
		self.sender = sms_sender.SmsSender()
		self.stop=False
#		self.leds= leds_handler.Leds()
	def start_thread(self):
		self.worker.setDaemon(True)
		self.worker.start()
		self.receiver.start_thread()
		self.sender.start_thread()
	def stop_thread(self):
		self.sms_queue.put(['stop',None])
	def send_message(self,message,nicknames=None,numbers=[]):
		phones=[]
		#logging.warning("SELECT phone_number FROM phone_book WHERE nickname  in ("+nicknames+");")
		if nicknames:
			phones=self.db.get_data_sql("SELECT phone_number,nickname FROM phone_book WHERE nickname  in ('"+nicknames.replace(",","','")+"');")
#		logging.warning(str(len(phones))+"f"+str(len(nicknames.split(","))))
			if len(phones)!=len(nicknames.split(",")):print("error='bad nickname'")
		if numbers:phones.extend([[phone,''] for phone in numbers])
		logging.warning(phones)
		if not phones:error='no number'
#		TODO:map(int,phones)error='bad number/len'
		logging.warning("SEND_SMS:("+",".join([phone+"("+nickname+")" for phone,nickname in phones])+")"+message)
		for phone,nickname in phones:
			pdu_msg=pdu.PDUSend(phone,message,nickname,self.db)
			if not config.DRY_RUN:self.sender.send_msg(pdu_msg,date_helper.date_to_string())
	def find_msg_id(self,sms,date):
		msg_ids=self.db.get_list_sql("select id from messages where reference_number="+str(sms.reference_number)+" and total_parts_number="+str(sms.total_parts_number)+" and phone_number='"+ sms.SenderPhoneNumber+"' and complete='n';") # (complete='n'?)'
		if len(msg_ids) == 0 : msg_id=-1
		elif len(msg_ids) == 1: msg_id=msg_ids[0]
#			ids_exist=self.db.get_list_sql("select DISTINCT msg_id from pdu where msg_id="+msg_id+" and sequence_part_number')
#			msg_ids-ids_exist
#			if len(msg_ids) > 1:
#				msg_ids=self.db.get_sql('from pdu where msg_id max(date)')
		elif len(msg_ids) > 1:msg_id=self.db.get_value_sql("SELECT id,max(date) from pdu where msg_id in ("+",".join(msg_ids)+")")
		return int(msg_id)
	def insert_new_sms(self,msg):
		new=None
		sms = pdu.PDUReceive(msg)
		adv=str(sms.reference_number)+","+str(sms.sequence_part_number)+"/"+str(sms.total_parts_number) if sms.total_parts_number > 1 else "1/1"
		logging.debug(sms.tpdu+","+sms.SenderPhoneNumber+","+date+","+sms.msg+","+adv)
		if sms.total_parts_number == 1:
			db_name=self.db.get_value_sql("SELECT nickname FROM phone_book WHERE phone_number='"+sms.SenderPhoneNumber+"';",True)
			msg_id=self.db.insert_row_and_get_id('INSERT INTO messages (msg, phone_number, date, phone_book_nickname) VALUES (?,?,?,?)',(sms.msg,sms.SenderPhoneNumber,sms.ServiceCenterDateStamp,db_name))
			self.db.run_sql('INSERT INTO pdus (pdu, date, msg_id) VALUES (?,?,?)',(sms.tpdu,sms.ServiceCenterDateStamp, msg_id))
			new=[sms.msg,sms.ServiceCenterDateStamp,sms.SenderPhoneNumber,db_name]
		else:
			msg_id=self.find_msg_id(sms,sms.ServiceCenterDateStamp)
			logging.debug('msg_id:'+str(msg_id))	
			if msg_id != -1:
				self.db.run_sql('INSERT INTO pdus (pdu, date, msg_id, sequence_part_number, tmp_msg) VALUES (?,?,?,?,?)',(sms.tpdu, sms.ServiceCenterDateStamp, msg_id, sms.sequence_part_number, sms.msg))
				if sms.total_parts_number == int(self.db.get_value_sql("SELECT count(id) from pdus where msg_id="+str(msg_id)+";")):
					msg="".join(self.db.get_list_sql("SELECT tmp_msg from pdus WHERE msg_id=" + str(msg_id) +" ORDER BY sequence_part_number"))
#					logging.debug(msg)
					self.db.run_sql("UPDATE messages SET msg = ? ,complete='y',status=1 WHERE id = ? ;",(msg,msg_id))
					self.db.run_sql("UPDATE pdus SET tmp_msg = Null WHERE msg_id = " + str(msg_id) +";")
					sms_date, db_name=self.db.get_data_sql('SELECT date, phone_book_nickname FROM messages WHERE id = ' + str(msg_id) +";")[0]
					new=[msg,sms_date, sms.SenderPhoneNumber,db_name]
			else:
				db_name=self.db.get_value_sql("SELECT nickname FROM phone_book WHERE phone_number='"+sms.SenderPhoneNumber+"';",True)
				msg_id=self.db.insert_row_and_get_id("INSERT INTO messages (phone_number, date, complete, total_parts_number, reference_number, phone_book_nickname) VALUES (?,?,'n',?,?,?)",(sms.SenderPhoneNumber,date,sms.total_parts_number, sms.reference_number, db_name))
				self.db.run_sql("INSERT INTO pdus (pdu, date, msg_id, sequence_part_number, tmp_msg) VALUES (?,?,?,?,?)",(sms.tpdu, date, msg_id, sms.sequence_part_number, sms.msg))
		return new
	def run(self):
		logging.debug('run...')
		self.db=sqlite_parser.sms_db()
		leds= leds_handler.Leds()
		while not self.stop:
			#logging.debug('before activity')
			activity, args = self.sms_queue.get()
			logging.debug(activity+str(args))
			#logging.debug('after activity')
			try:
				if activity == 'stop':
					logging.debug('get stop.')
					self.stop = True
				elif activity == 'send_msg':
					numbers=nicknames=None
					if args.startswith(b'p:'):
						index=args.find(b'\n')
						numbers=args[2:index].decode("utf8").split(',')
						args=args[index+1:]
					if args.startswith(b'n:'):
						index=args.find(b'\n')
						nicknames=args[2:index].decode("utf8")
						args=args[index+1:]
					if not args.startswith(b'm:'):raise helpers.ModemError("bad msg format"+str(args))
					self.send_message(args[2:].decode("utf8"),nicknames,numbers)
				elif activity == 'receive_new_msg':
					logging.info(activity)
					inform_msg=self.insert_new_sms(args)
					if inform_msg:
						vibrator.vibrate()
						leds.set_leds(leds_handler.LedName.BLUE,leds_handler.LedAction.SET,255)
						message,date,phone,nickname=inform_msg
						if not nickname: nickname=""
						logging.warning("GET_SMS:"+phone+"("+nickname+")"+message)
				else:raise helpers.ModemError("bad activity"+activity)
			except Exception as e:
				logging.error(traceback.format_exc())
			self.sms_queue.task_done()
		self.receiver.stop_thread()
		self.sender.stop_thread()
		self.db=None
#		logging.debug("stoped")
	def __del__(self):
		self.close()
	def close(self):
		self.worker.join()
		self.receiver.close()
		self.sender.close()
		logging.info("closed")
