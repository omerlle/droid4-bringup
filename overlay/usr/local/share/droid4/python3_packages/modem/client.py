#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import socket
import sys
import time
import subprocess
from enum import Enum

import argparse
import utils.date_helper as date_helper
import modem.software.db_manager as sqlite_parser
import modem.software.modem_helpers as helpers
import modem.config.app_config as config
import hardware.led_handler as leds
import utils.sqlite_helper

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

server_address = '/tmp/droid4_modem/server'

class MessageStatus(Enum):
	UNREAD=1
	READ=2
	SEND=3
	SEND_FAIL=4
class CallsStatus(Enum):
	INCOMING=1
	DIAL=2
	MISS=3
class Client():
	def __init__(self):
		self.sock = None
		self.db=utils.sqlite_helper.SqliteHelper(config.DATABASE_FILENAME)
	def quit_modem(self):
		self.send('stop')
	def set_modem(self,state):
		self.send('phone modem ' + state)
	def set_modem_update_status(self,state):
		self.send('phone status ' + state)
	def answer(self):
		self.send('phone answer')
	def hangup(self):
		self.send('phone hangup')
	def send_sms(self,message, phones=None, nicknames=None):
		msg="send\n"
		if phones:msg=msg+'p:'+",".join(phones)+"\n"
		if nicknames:msg=msg+'n:'+",".join(nicknames)+"\n"
		msg=msg+'m:'+message
#	       print(msg)
		self.send(msg)
	def make_call(self,privileged,is_nickname,phone):
		msg="phone call "
		if privileged:msg=msg+'p '
		if is_nickname: msg=msg+'n '
		self.send(msg+"s:"+phone)
	def send(self,string):
		if not self.sock:self.connect_socket()
		try:
#"".join("{:02x}".format(ord(c)) for c in message)
			msg=string.encode()
			length=len(msg)
			size=(length.bit_length() + 7) // 8
			header_size=int(size)
#			message=chr(int('ff',16))+chr(int('15',16))+chr(header_size)+chr(int(size,16))+string
			message=b'\xff\x15'+ bytes([header_size])+length.to_bytes(size, 'big')+msg
			print('sending:'+str(message))
			self.sock.sendall(message)
		except( socket.error, msg):
			self.sock.close()
			sys.exit(1)
	def connect_socket(self):
		if self.sock: raise
		# Create a UDS socket
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

		# Connect the socket to the port where the server is listening
		print('connecting to ' + server_address)
		try:
			self.sock.connect(server_address)
	#	       self.sock.setblocking(1)
		except( self.socket.error, msg):
			print >>sys.stderr, msg
#			sys.exit(1)
	def close_socket(self):
		if not self.sock: raise
		print('closing socket')
		self.sock.close()
		self.sock =None
	def __del__(self):
			time.sleep(1)
			if self.sock:self.close_socket()
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
#			print('SELECT '+fileds+' FROM messages INNER JOIN message_status ON message_status.id = messages.status'+where+' ORDER BY voice_call_list.date DESC;')
			for id,phone_number,msg,phone_book_nickname, date, status in self.db.get_data_sql('SELECT '+fileds+' FROM messages INNER JOIN message_status ON message_status.id = messages.status' + where +' ORDER BY date DESC '+  limit + ';'):
				print("("+str(id)+")"+phone_number+":"+str(phone_book_nickname)+":"+date+":"+status+":"+msg)
#			print('UPDATE messages SET status='+str(MessageStatus.READ.value) + where + ' AND status=' + str(MessageStatus.UNREAD.value) + limit + ';')
			if mark: self.db.run_sql('UPDATE messages SET status='+str(MessageStatus.READ.value) + where + ' AND status=' + str(MessageStatus.UNREAD.value) +  limit + ';')
	def show_phonebook(self, fileds, full=False,ids=[],phones=[],names=[],nicknames=[],last_names=[],subject=None,print_data=True):
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
#		print('SELECT '+fileds+' FROM phone_book'+where+';')
		ans = self.db.get_data_sql('SELECT '+fileds+' FROM phone_book'+where+';')
		if print_data:
			for row in ans:
				print(":".join(map(str,row)))
		else: return None if not ans else ans[0][0]
	def edit_phonebook(self, id, phone=None, name=None, nickname=None, last_name=None, subject=None, description=None, update_date=False):
		sql_set=[]
		if phone: sql_set.append("phone_number='"+phone+"'")
		if nickname: sql_set.append("first_name='"+name+"'")
		if nickname: sql_set.append("nickname='"+nickname+"'")
		if nickname: sql_set.append("last_name='"+last_name+"'")
		if subject: sql_set.append("subject='"+subject+"'")
		if description: sql_set.append("description='"+description+"'")
		if update_date:sql_set.append("date='"+date_helper.date_to_string()+"'")
		self.db.run_sql('UPDATE phone_book SET '+ ",".join(sql_set) + ' WHERE id=' + str(id) + ';')
	def update_phonebook_lists(self, update_phone_list, update_nickname_list):
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
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='cli for droid4_modem.')
	parser.set_defaults(cmd=None)
	parser.add_argument('-q','--quit', help="close droid4_modem", action='store_true')
	parser.add_argument('-a','--answer', help="answer for voice call", action='store_true', default=None)
	parser.add_argument('-g','--hangup', help="hanging up", dest='answer', action='store_false')
	parser.add_argument('-m','--modem', help="set the modem offline/online", action='store',choices=['off', 'on'])
	parser.add_argument('-s','--status', help="set the network strength offline/online", action='store',choices=['off', 'on'])
	parser.add_argument('-o','--old', help="turn the new led(blue) off", action='store_true')
	subparsers = parser.add_subparsers(help='modem command')
#	quit_parser = subparsers.add_parser('quit', help='close droid4_modem')
#	quit_parser.set_defaults(cmd="quit")
	sms_parser = subparsers.add_parser('sms', help='show sms list')
	sms_parser.set_defaults(status=[])
	sms_parser.add_argument('-u','--unread', help="show unread sms", dest='sms_type', action='append_const', const=MessageStatus.UNREAD)
	sms_parser.add_argument('-r','--read', help="show read sms", dest='sms_type', action='append_const', const=MessageStatus.READ)
	sms_parser.add_argument('-s','--send', help="show send sms", dest='sms_type', action='append_const', const=MessageStatus.SEND)
	sms_parser.add_argument('-f','--fail', help="show send failed sms", dest='sms_type', action='append_const', const=MessageStatus.SEND_FAIL)
	sms_parser.add_argument('-i','--id', help="sms id", default=[], dest='ids', type=int, nargs='*')
	sms_parser.add_argument('-n','--nickname', help="names for sms", default=[], dest='nicknames', action='append')
	sms_parser.add_argument('-p','--phone', help="phones for sms", default=[], dest='phones', action='append')
	sms_parser.add_argument('-l','--length', help="sms list length", type=int, action='store')
	sms_parser.add_argument('-m','--mark', help="mark unread sms that select as read",action='store_true')
	sms_parser.add_argument('--delete', help="delete selected sms",action='store_true')
	sms_parser.set_defaults(cmd="sms")
	history_parser = subparsers.add_parser('history', help='show call history')
	history_parser.add_argument('-m','--miss', help="show miss calls", dest='call_type', action='append_const', const=CallsStatus.MISS)
	history_parser.add_argument('-d','--dial', help="show dial calls", dest='call_type', action='append_const', const=CallsStatus.DIAL)
	history_parser.add_argument('-i','--incoming', help="show incoming calls", dest='call_type', action='append_const', const=CallsStatus.INCOMING)
	history_parser.add_argument('-l','--length', help="history list length", type=int, action='store')
	history_parser.add_argument('-n','--nickname', help="names for history list", default=[], dest='nicknames', action='append')
	history_parser.add_argument('-p','--phone', help="phones for history list", default=[], dest='phones', action='append')
	history_parser.set_defaults(cmd="history")
	phonebook_parser = subparsers.add_parser('phonebook', help='phonebook')
	phonebook_subparsers = phonebook_parser.add_subparsers(help='phonebook action')
	del_phonebook_parser = phonebook_subparsers.add_parser('del', help='delete from phonebook').add_mutually_exclusive_group()
	del_phonebook_parser.add_argument('-i','--id', help="row id", action='store', type=int)
	del_phonebook_parser.add_argument('-p','--phone', help="phone", action='store')
	del_phonebook_parser.add_argument('-n','--nickname', help="nickname", action='store')
	del_phonebook_parser.set_defaults(action="del")
	add_phonebook_parser = phonebook_subparsers.add_parser('add', help='add new nickname to phonebook')
	add_phonebook_parser.add_argument('name', help="name to add", action='store')
	add_phonebook_parser.add_argument('phone', help="phone to add", action='store')
	add_phonebook_parser.add_argument('-n','--nickname', help="add nickname field", action='store')
	add_phonebook_parser.add_argument('-l','--lastname', help="add last name field", action='store')
	add_phonebook_parser.add_argument('-s','--subject', help="add subject field", action='store')
	add_phonebook_parser.add_argument('-d','--description',help="add description field", action='store')
	add_phonebook_parser.set_defaults(action="add")
	edit_phonebook_parser = phonebook_subparsers.add_parser('edit', help='edit phonebook')
	edit_phonebook_parser.add_argument('id', help="row id for edit", action='store', type=int)
	edit_phonebook_parser.add_argument('-p','--phone', help="edit phone", action='store')
	edit_phonebook_parser.add_argument('-k','--nickname', help="edit nickname", action='store')
	edit_phonebook_parser.add_argument('-l','--lastname', help="edit last name", action='store')
	edit_phonebook_parser.add_argument('-n','--name', help="edit name", action='store')
	edit_phonebook_parser.add_argument('-s','--subject', help="edit subject", action='store')
	edit_phonebook_parser.add_argument('-d','--description',help="edit description", action='store')
	edit_phonebook_parser.add_argument('-t','--time',help="update date field", action='store_true')
	edit_phonebook_parser.set_defaults(action="edit")
	show_phonebook_parser = phonebook_subparsers.add_parser('show', help='show phonebook')
	show_phonebook_parser.add_argument('-i','--id', help="show id in phonebook",  default=[], dest='ids', action='append', type=int)
	show_phonebook_parser.add_argument('-d','--description',help="show description field", action='store_true')
	show_phonebook_parser.add_argument('-t','--time',help="show update time field", action='store_true')
	show_phonebook_parser.add_argument('-p','--phone', help="show phonebook with phones", default=[], dest='phones', action='append')
	show_phonebook_parser.add_argument('-n','--name', help="show phonebook with names", default=[], dest='names', action='append')
	show_phonebook_parser.add_argument('-k','--nickname', help="show phonebook with nicknames", default=[], dest='nicknames', action='append')
	show_phonebook_parser.add_argument('-l','--lastname', help="show phonebook with last names", default=[], dest='lastnames', action='append')
	show_phonebook_parser.add_argument('-s','--subject', help="show subject that start with the pattern", action='store')
	show_phonebook_parser.add_argument('-f','--full', help="show only full pattern", action='store_true')
	show_phonebook_parser.set_defaults(action="show")
	update_phonebook_parser = phonebook_subparsers.add_parser('update', help='update phonebook lists')
	update_phonebook_parser.add_argument('-n','--nickname', help="update nickname list by phonebook",  action='store_true')
	update_phonebook_parser.add_argument('-l','--list', help="update phone list by phonebook",  action='store_true')
	update_phonebook_parser.set_defaults(action="update")
	phonebook_parser.set_defaults(cmd="phonebook")
	phonebook_parser.set_defaults(action=None)
	call_parser = subparsers.add_parser('call', help='voice call')
	call_parser.set_defaults(cmd="call")
	call_parser.add_argument('-n','--nickname', help="use name instead of phone for call", action='store_true')
	call_parser.add_argument('-p','--privileged', help="don't show the number", action='store_true')
	call_parser.add_argument('phone', help="phone for call")
	send_parser = subparsers.add_parser('send', help='send sms')
	send_parser.add_argument('-n','--nickname', help="names for action", default=[], dest='nicknames', action='append')
	send_parser.add_argument('-p','--phone', help="phones for action", default=[], dest='phones', action='append')
	send_parser.add_argument('send_message', help="text for send")
	send_parser.set_defaults(cmd="send")
	args = parser.parse_args()
#	print(args)
	if args.cmd and args.cmd == "send" and not args.phones and not args.nicknames:
		print('miss at least one phone number or nickname')
		send_parser.print_usage()
		exit(-1)
	if args.cmd and args.cmd == "phonebook" and not args.action:
		print('miss action')
		phonebook_parser.print_usage()
		exit(-1)
	if args.cmd and args.cmd == "phonebook" and args.action == "edit" and not (args.phone or args.nickname or args.subject or args.description or args.time):
		print('miss filed for update')
		edit_phonebook_parser.print_usage()
		exit(-1)
	if args.cmd and args.cmd == "phonebook" and args.action == "update" and not (args.list or args.nickname):
		print('miss list for update')
		update_phonebook_parser.print_usage()
		exit(-1)
	cel_modem=Client()
	if args.old:leds.Leds().set_leds(leds.LedName.BLUE,leds.LedAction.TURN_OFF)
	if args.modem:cel_modem.set_modem(args.modem)
	if args.answer != None:cel_modem.answer() if args.answer else cel_modem.hangup()
	if args.status:cel_modem.set_modem_update_status(args.status)
	if args.cmd:
		if args.cmd == "sms":cel_modem.sms_handle(args.mark, args.sms_type,args.ids,args.nicknames,args.phones, args.length, args.delete)
		elif args.cmd == "history":cel_modem.print_call_history(args.call_type, args.nicknames, args.phones, args.length)
		elif args.cmd == "send":
			cel_modem.send_sms(args.send_message,args.phones,args.nicknames)
		elif args.cmd == "call":cel_modem.make_call(args.privileged,args.nickname,args.phone)
		elif args.cmd == "phonebook":
			if args.action == 'del':
				if args.id:cel_modem.db.run_sql('DELETE FROM phone_book WHERE id = ' + str(args.id) + ';')
				elif args.phone:cel_modem.db.run_sql("DELETE FROM phone_book WHERE phone_number = '" + args.phone + "';")
				elif args.nickname:cel_modem.db.run_sql("DELETE FROM phone_book WHERE nickname ='"+args.nickname+"' ;")
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
				cel_modem.db.run_sql(prefix+suffix+");")
			elif args.action == 'show':
				fileds='id, phone_number, nickname, first_name, last_name, subject, description' if args.description else 'id, phone_number, nickname, first_name, last_name, subject'
				if args.time:fileds=fileds+', date'
				cel_modem.show_phonebook(fileds,args.full,args.ids,args.phones,args.names,args.nicknames,args.lastnames,args.subject)
			elif args.action == 'edit':cel_modem.edit_phonebook(args.id, args.phone, args.name, args.nickname, args.lastname, args.subject, args.description, args.time)
			elif args.action == 'update':cel_modem.update_phonebook_lists(args.list, args.nickname)
			else:print("error:bad cmd-"+args.action)
		else:print("error:bad cmd-"+args.cmd)
	if args.quit:cel_modem.quit_modem()
