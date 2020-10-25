#!/usr/bin/python
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

from config import app_config
from software import mamagers_client
import os
import string
import traceback
import logging
import threading
from queue import Queue
import software.modem_helpers as helpers

class NotifyManager:
	def __init__(self):
		self.worker=threading.Thread(name="notify_manager_worker",target=self.run)
		self.stop=False
		self.queue=mamagers_client.managers_queues[mamagers_client.managers.notifier.value]
		self.notify_pipe=None
	def start_thread(self):
		self.worker.setDaemon(True)
		self.worker.start()
	def stop_thread(self):
		self.queue.put(['stop',None])
	def notify_user(self,action,details="",body=""):
			lines=1
			if details:
				lines=lines+1
				details="details: "+details+"\n"
			if body: 
				lines=lines+len(body.splitlines())
				body=body+"\n"
			msg="lines:"+str(lines)+"\naction:"+action+"\n"+details+body
			logging.debug('write...')
			self.notify_pipe.write(msg)
			logging.debug('finish')
	def run(self):
		logging.debug('run...')
		if not os.path.exists(app_config.NOTIFICATION_FILENAME):
			os.mkfifo(app_config.NOTIFICATION_FILENAME)
		self.notify_pipe=open(app_config.NOTIFICATION_FILENAME, "w",buffering=1)
		logging.debug('opened')
		while not self.stop:
			#logging.debug('before activity')
			activity, details = self.queue.get()
			#logging.debug('after activity')
			try:
				if activity == 'stop':
					self.stop = True
				elif activity == 'at_answer':self.notify_user(activity,details)
				elif activity == 'call_status':self.notify_user(activity," ".join(details))
				elif activity == 'got_call':self.notify_user(activity," ".join(details))
				elif activity == 'got_new_sms':self.notify_user(activity," ".join(details[0:3]),details[3])
			except Exception as e:
				logging.error(traceback.format_exc())
		self.notify_pipe.close()
	def close(self):
		self.worker.join()
		logging.info("closed")
	def __del__(self):
		self.close()
