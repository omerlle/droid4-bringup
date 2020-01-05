#!/usr/bin/python3

import logging

import utils.date_helper

import software.mamagers_client as clients
import config.app_config as config
import software.sms.handler as sms_manager
import software.server as server_manager
import software.modem_managment as modem_manager

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

if __name__ == '__main__':
	stop = False
	logging.basicConfig(filename=config.LOG_PATH_PREFIX+date_helper.date_to_string()+'_modem_app.log',level=logging.DEBUG,format='[%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d:(%(threadName)-10s)]:%(asctime)s|%(message)s',)
	logging.getLogger('shiloch_phone.shiloch_phone.Manager')

	server = server_manager.ModemServer()
	sms = sms_manager.SmsManager()
	modem = modem_manager.ModemManager()
	
	sms.start_thread()
	server.start_thread()
#       manager.start_thread()
	modem.start_thread()
	manager_queue=clients.managers_queues[clients.managers.manager.value]
	print('run..')
	while not stop:
		command = manager_queue.get()
		logging.debug(command)
		if (command[0]=='client_command'):
			if ( command[2]== 'stop'):
				logging.info("fd:"+str(command[1])+" send stop to manager. stopping...")
				stop = True
				server.stop_thread()
				sms.stop_thread()
				modem.stop_thread()
		else: raise helpers.ModemError("bad command"+str(command))
		manager_queue.task_done()
	del server
	del sms
	del modem
	logging.info("exit")
#       sms= None
