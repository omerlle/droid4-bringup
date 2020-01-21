# -*- coding: utf-8 -*-
import os
import traceback
import logging
import select
import threading
import queue
import utils.date_helper as date_helper
from enum import Enum
import config.app_config as config
import software.mamagers_client as clients
import software.modem_helpers as helpers
import software.db_manager as sqlite_parser
import software.db_manager as sqlite_parser
import hardware.led_handler as leds_handler
import hardware.vibrator as vibrator

class VoiceCallCmd(Enum):
	STOP=0
	INCOMING_CALL=1
	ANSWER=2
	HENGUP=3
	CALL=4
class VoiceCallStatus(Enum):                                                                                     
        IDLE=0                                                                                       
        WAIT_FOR_ANSWER=1                                                                                       
        CONVERSATION=2                                                                                              
        INCOMING_CALL=3
class ModemManager:
	def __init__(self):
		self.modem_queue=clients.managers_queues[clients.managers.modem.value]
		self.worker=threading.Thread(name="modem_manager_worker",target=self.run)
		self.poll_modem_worker =threading.Thread(name="read_modem_worker",target=self.poll_modem)
		self.call_worker =threading.Thread(name="voice_call_manager",target=self.voice_call_manager)
		self.poll_modem_pipe_read, self.poll_modem_pipe_write = os.pipe()
		self.stop=False
		self.db=None
		self.voice_call_queue = queue.Queue()
		self.last_call=''
		self.status=VoiceCallStatus.IDLE 
	def start_thread(self):
		self.worker.setDaemon(True)
		self.worker.start()
		self.poll_modem_worker.setDaemon(True)
		self.poll_modem_worker.start()
		self.call_worker.setDaemon(True)
		self.call_worker.start()
	def stop_thread(self):
		clients.ModemClient().stop()
		self.voice_call_queue.put(VoiceCallCmd.STOP)
	def poll_modem(self):
		modem_read = open(config.MODEM_DEV,"r")
		logging.info('MODEM READY.')
		modem_client=clients.ModemClient()
		while not self.stop:
				try:
					line = modem_read.readline().rstrip()
					modem_client.modem_got(line)
				except Exception as e:
					logging.error(traceback.format_exc())
		modem_read.close()
	def write_to_modem(cmd):
		with open(config.MODEM_DEV, "w") as dev:
			dev.write(cmd+"\r\n")
	def voice_call_manager(self):
		stop=False
		timeout=None
		leds= leds_handler.Leds()
#		db=sqlite_parser.sms_db()
#		db.voice_call_status(IDLE)
		status=VoiceCallStatus.IDLE
		while not stop:
			try:
				cmd = self.voice_call_queue.get(timeout=timeout)
				if cmd == VoiceCallCmd.STOP:
					logging.debug('get stop.')
					self.stop = True
				elif cmd == VoiceCallCmd.INCOMING_CALL:
#					db.voice_call_status(INCOMING_CALL)
					status=VoiceCallStatus.INCOMING_CALL
					leds.set_leds(leds_handler.LedName.RED,leds_handler.LedAction.SET,255)
					vibrator.vibrate(300)                                                                            
					timeout=1
				elif cmd == VoiceCallCmd.ANSWER:
#					db.voice_call_status(CONVERSATION)
					status=VoiceCallStatus.CONVERSATION
					timeout=None
				elif cmd == VoiceCallCmd.HENGUP:
#					db.voice_call_status(HANGUP)
					leds.set_leds(leds_handler.LedName.RED,leds_handler.LedAction.SET,0)
					status=VoiceCallStatus.IDLE
					timeout=None
				elif cmd == VoiceCallCmd.CALL:
#					db.voice_call_status(WAIT_FOR_ANSWER)
					status=VoiceCallStatus.WAIT_FOR_ANSWER
					leds.set_leds(leds_handler.LedName.RED,leds_handler.LedAction.SET,255)
					timeout=None
				logging.info('MOVE_STATE'+str(status))
			except queue.Empty:
				vibrator.vibrate(300)
			except Exception as e:                                                      
				logging.error(traceback.format_exc())
	def update_db_with_conversation(self,status):
		if self.last_call:
			self.db.run_sql('INSERT INTO voice_call_list (phone,date,status) VALUES(?,?,?)',(self.last_call, date_helper.date_to_string(), status));
			self.last_call = None
	def run(self):
		logging.debug('run...')
		self.db=sqlite_parser.sms_db()
		while not self.stop:
			cmd,activity = self.modem_queue.get()
			try:
				if cmd == 'stop':
					logging.debug('get stop.')
					self.stop = True
				elif cmd == 'm':
					line=activity
					logging.debug("Got line:"+line)	
					if line.startswith("~+RSSI="):pass
					elif line.startswith("~+CREG="):pass
					elif line.startswith("~+GSYST="):pass
					elif line == "~+WAKEUP":
						pass
					elif line.startswith("~+CLIP=\""):
						self.last_call = line.split('"', 2)[1]
						nickname=self.db.get_value_sql("SELECT nickname FROM phone_book WHERE phone_number='"+self.last_call+"';",True)
						line="GOT CALL, NUMBER:"+self.last_call+"("+str(nickname)+")"
						logging.debug(line)
						with open("/dev/tty1", "w") as dev:
							dev.write(line)
					elif line == "H:OK":self.update_db_with_conversation(1)
					elif line.startswith("~+CIEV="):
						if line == "~+CIEV=1,4,0":self.voice_call_queue.put(VoiceCallCmd.INCOMING_CALL)
						elif line == "~+CIEV=1,2,0":
							self.voice_call_queue.put(VoiceCallCmd.ANSWER)
							self.update_db_with_conversation(1)
						elif line == "~+CIEV=1,1,0":
							self.voice_call_queue.put(VoiceCallCmd.CALL)
							self.update_db_with_conversation(2)
						elif line == "~+CIEV=1,0,0" or line == "~+CIEV=1,0,4":
							self.voice_call_queue.put(VoiceCallCmd.HENGUP)
							if self.last_call:
								self.update_db_with_conversation(3)
								leds_handler.Leds().set_leds(leds_handler.LedName.BLUE,leds_handler.LedAction.SET,255)
						elif line == "~+CIEV=1,3,0" or line == "~+CIEV=1,7,0":pass
#						else:raise helpers.ModemError('bad ~+CIEV:"'+line+"'")
						else:logging.error('Traceback bad ~+CIEV:"'+line+"'")
					elif line == "":
						logging.debug("Got empty line")
					elif line == "+CFUN:OK" or line == "+SCRN:OK" or "H:ERROR" or "D:OK" or "A:OK":pass
					else:raise helpers.ModemError('bad line:"'+line+"'")
				elif cmd == 'from_client':
					if activity.startswith('modem'):
						cmd="AT+CFUN=1" if activity=='modem on' else "AT+CFUN=0"
						ModemManager.write_to_modem(cmd)
					elif activity.startswith('status'):
						state="1" if activity=='status on' else "0"
						ModemManager.write_to_modem('AT+SCRN='+state)
					elif activity == 'answer':
						ModemManager.write_to_modem("ATA")
					elif activity == 'hangup':
						ModemManager.write_to_modem("ATH")
					elif activity.startswith('call'):
						nickname=False
						if activity[4:7] == " p ":
							line_id=",1"
							activity=activity[6:]
						else:
							activity=activity[4:]
							line_id=",0"
						if activity[:3] == " n ":
							nickname=True
							activity=activity[2:]
						if not activity.startswith(" s:"):raise helpers.ModemError("bad format:"+activity)
						phone = activity[3:]
						if nickname:phone = self.db.get_value_sql("SELECT phone_number FROM phone_book WHERE nickname='"+phone+"';")
						self.last_call = phone
						logging.info('try to call:'+phone)
						ModemManager.write_to_modem("ATD+"+phone+line_id)
					else:raise helpers.ModemError("bad activity"+activity)
				else:raise helpers.ModemError("bad cmd"+cmd)
			except Exception as e:
				logging.error(traceback.format_exc())
			self.modem_queue.task_done()
#		logging.debug("stoped")
	def __del__(self):
		self.close()
	def close(self):
		self.worker.join()
		self.poll_modem_worker.join()
		self.voice_call_queue.join()
		logging.info("closed")
