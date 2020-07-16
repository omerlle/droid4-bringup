# -*- coding: utf-8 -*-
import config.app_config as config
#import software.db_manager as db
import software.mamagers_client as clients
import string
import traceback
import logging
import threading
import select
import software.modem_helpers as helpers
import queue
import os
import re
#import Set
class SmsReceiver:
	def __init__(self):
		self.sms_client = clients.SmsClient()
		self.worker=threading.Thread(name="receiver_worker",target=self.run)
		self.pipe_read, self.pipe_write = os.pipe()
		self.sms_len=0
	def start_thread(self):
		self.worker.setDaemon(True)
		self.worker.start()
	def stop_thread(self):
		os.write(self.pipe_write,b's')
	def run(self):
		poll=select.poll()
		poll.register(self.pipe_read,select.POLLIN)
		logging.debug('bere_open '+config.INCOMING_SMS_FILENAME)
		self.incoming_sms=os.open(config.INCOMING_SMS_FILENAME,os.O_RDONLY)
		logging.debug('self.incoming_sms'+str(self.incoming_sms))
		poll.register(self.incoming_sms,select.POLLIN)
		logging.debug('after_open')
		logging.debug('SMS READY')
		if config.INIT_MODEM:
			modem=clients.ModemClient()
			modem.do_cmd('modem on')
			modem.do_cmd('status off')
		new_line=b'\n'
		output=b''
		stop = False
		while not stop:
			events=poll.poll(-1)
			for fd,event in events:
#				logging.debug('fd:'+str(fd)+", event:"+str(event))
				if fd == self.pipe_read:
					if event == select.POLLIN:
						data=os.read(self.pipe_read,1)
						if data==b's':
							stop = True
							logging.debug("get_stop")
						else: raise helpers.ModemError("bad sighn:"+str(data))
					else: raise helpers.ModemError("error"+str(event))
				elif fd == self.incoming_sms:
					if event == select.POLLIN:
						try:
#							logging.debug("before read")
							data=os.read(self.incoming_sms,2048)
							logging.debug("modem log \""+str(data)+"\"")
							output=output+data
							index=output.find(new_line)
							while index>0:
								word=output[:index]
								output=output[index+1:]
#								logging.debug("word:\""+str(word)+"\"")
								current_len = self.sms_len
								self.sms_len = 0
								if re.search(b'^U[0-9]{4}', word):
									if word[5:]==b'+GCNMA=OK':logging.debug("log-get-awk:"+str(word))
									elif word[5:].startswith(b'~+GCMT='):self.sms_len = int(word[12:])
								elif word.startswith(b'07917952') and current_len:
									if len(word)!=current_len:logging.error("bad len")
									with open(config.INCOMING_SMS_FILENAME,'w') as awk:
										awk.write("U0000AT+GCNMA=1\r")
									self.sms_client.receive_new_msg(word)
								else:logging.error("get unknoun msg:"+str(word))
								index=output.find(new_line)
						except Exception as e:
							logging.error(traceback.format_exc())
					else: raise helpers.ModemError("error"+str(event))
				else:raise helpers.ModemError("error bad fd"+str(fd))
		os.close(self.incoming_sms)
		self.incoming_sms=None
#		logging.debug("stoped")
	def __del__(self):
		if self.incoming_sms: os.close(self.incoming_sms)
	def close(self):
		self.worker.join()
		logging.info("closed")
