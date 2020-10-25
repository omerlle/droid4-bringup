#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

#from Queue import Queue
import queue
from enum import Enum
import software.modem_helpers as helpers

managers = Enum('managers', 'manager server db sms sender caller notifier modem')
managers_queues=[]
for i in range(0,len(managers)+1):
  managers_queues.append(queue.Queue())
class ManagerClient:
	def __init__(self):
		self.queue = managers_queues[managers['manager'].value]
	def client_command(self, fd, command):
		self.queue.put(['client_command',fd,command])
class ServerClient:
	def __init__(self, server_queue):
		self.server_queue=server_queue
	def send(self, message):
		self.server_queue.put(message)
class SmsClient:
	def __init__(self):
		self.queue=managers_queues[managers.sms.value]
	def send_msg(self, arg):
		self.queue.put(('send_msg',arg))
	def receive_new_msg(self, sms):
		self.queue.put(('receive_new_msg',sms))
class NotifyClient:
	def new_call(phone,date,nickname):
                managers_queues[managers.notifier.value].put(['got_call',[phone,date,nickname]])
	def new_sms(phone,date,nickname,message):
		managers_queues[managers.notifier.value].put(['got_new_sms',[phone,date,nickname,message]])
	def at_answer():
		managers_queues[managers.notifier.value].put(['at_answer','OK'])
	def call_status_updated(status,phone,date):
		managers_queues[managers.notifier.value].put(['call_status',[phone,date,str(status)]])
class ModemClient:
	def __init__(self):
		self.queue=managers_queues[managers.modem.value]
	def modem_got(self, line):
		self.queue.put(('m',line))
	def do_cmd(self, cmd):
		self.queue.put(('from_client',cmd))
	def stop(self):
		self.queue.put(('stop',None))
