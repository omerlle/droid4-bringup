#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import logging

import utils.date_helper as date_helper
import modem_wrapper.software.wrapper as wrapper
import modem_wrapper.software.helpers as helpers
import modem_wrapper.software.get_opt as opt
import modem_wrapper.config.app_config as config
import hardware.led_handler as leds
import utils.sqlite_helper

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

if __name__ == '__main__':
	logging.basicConfig(filename=config.LOG_PATH_PREFIX+date_helper.date_to_string(format=date_helper.DateStringFormat.FILENAME)+'_modem_app.log',level=logging.DEBUG,format='[%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d]:%(asctime)s|%(message)s',)
	logging.getLogger('droid4.modem_wrapper')
	args=opt.get_opt()
	modem_wrapper=wrapper.ModemWrapper()
	if args.clear:modem_wrapper.clear_notify()
	if args.notify:modem_wrapper.notify_updated(first_line=True)
	if args.modem:modem_wrapper.write_to_modem("AT+CFUN=1" if args.modem == 'on' else "AT+CFUN=0")
	if args.answer != None:modem_wrapper.write_to_modem("ATA" if args.answer else "ATH")
	if args.status:modem_wrapper.write_to_modem('AT+SCRN=1' if args.status == 'on' else "AT+SCRN=0")
	if args.cmd:
		if args.cmd == "system":
			if args.line.startswith('0791'):modem_wrapper.receive_new_msg(args.line)
			else:modem_wrapper.modem_cmd(args.line)
		elif args.cmd == "sms":modem_wrapper.sms_handle(args.mark, args.sms_type,args.ids,args.nicknames,args.phones, args.length, args.delete)
		elif args.cmd == "history":modem_wrapper.print_call_history(args.call_type, args.nicknames, args.phones, args.length)
		elif args.cmd == "send":
			modem_wrapper.send_sms(args.send_message,args.phones,args.nicknames)
		elif args.cmd == "dials":modem_wrapper.dials(args.privileged,args.nickname,args.phone)
		elif args.cmd == "phonebook":
			if args.action == 'del':
				if args.id:modem_wrapper.db.run_sql('DELETE FROM phone_book WHERE id = ' + str(args.id) + ';')
				elif args.phone:modem_wrapper.db.run_sql("DELETE FROM phone_book WHERE phone_number = '" + args.phone + "';")
				elif args.nickname:modem_wrapper.db.run_sql("DELETE FROM phone_book WHERE nickname ='"+args.nickname+"' ;")
			elif args.action == 'add':
				prefix="INSERT INTO phone_book (date, phone_number, first_name"
				suffix=") VALUES('"+date_helper.date_to_string()+"','"+args.phone+"','"+args.name+"'"
				if args.nickname:
					prefix=prefix+",nickname"
					suffix=suffix+",'"+args.nickname+"'"
				if args.lastname:
					prefix=prefix+",last_name"
					suffix=suffix+",'"+args.lastname+"'"
				if args.subject:
					prefix=prefix+",subject"
					suffix=suffix+",'"+args.subject+"'"
				if args.description:
					prefix=prefix+",description"
					suffix=suffix+",'"+args.description+"'"
				modem_wrapper.db.run_sql(prefix+suffix+");")
			elif args.action == 'show':
				fileds='id, phone_number, nickname, first_name, last_name, subject, description' if args.description else 'id, phone_number, nickname, first_name, last_name, subject'
				if args.time:fileds=fileds+', date'
				modem_wrapper.show_phonebook(fileds,args.full,args.ids,args.phones,args.names,args.nicknames,args.lastnames,args.subject)
			elif args.action == 'edit':modem_wrapper.edit_phonebook(args.id, args.phone, args.name, args.nickname, args.lastname, args.subject, args.description, args.time)
			elif args.action == 'update':modem_wrapper.update_phonebook_lists(args.list, args.nickname)
			else:print("error:bad cmd-"+args.action)
		else:print("error:bad cmd-"+args.cmd)
