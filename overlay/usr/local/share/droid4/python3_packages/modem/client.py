#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
import time
from enum import Enum

import argparse
import datetime

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
		if args.nicknames:msg=msg+'n:'+",".join(nicknames)+"\n"
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
#			print('SELECT '+fileds+' FROM messages INNER JOIN message_status ON message_status.id = messages.status'+where+';')
			for id,phone_number,msg,phone_book_nickname, date, status in self.db.get_data_sql('SELECT '+fileds+' FROM messages INNER JOIN message_status ON message_status.id = messages.status' + where + limit + ';'):
				print("("+str(id)+")"+phone_number+":"+str(phone_book_nickname)+":"+date+":"+status+":"+msg)
#			print('UPDATE messages SET status='+str(MessageStatus.READ.value) + where + ' AND status=' + str(MessageStatus.UNREAD.value) + limit + ';')
			if mark: self.db.run_sql('UPDATE messages SET status='+str(MessageStatus.READ.value) + where + ' AND status=' + str(MessageStatus.UNREAD.value) +  limit + ';')
	def show_phonebook(self, full=False,ids=[],phones=[],nicknames=[],subject=None,description=False,date=False):
		fileds='id, phone_number, nickname, subject, description' if description else 'id, phone_number, nickname, subject'
		if date:fileds=fileds+', date'
		where=""
		if ids or phones or nicknames or subject:
			sql_or=[]
			if ids:sql_or.append("id IN ("+",".join(map(str,ids))+")")
			if phones:
				phone_where="phone_number IN ("+",".join(phones)+")" if full else "phone_number LIKE '" + "%' OR phone_number LIKE '".join(phones)+"%'"  
				sql_or.append(phone_where)
			if nicknames:
				nickname_where="nickname IN ('"+"','".join(nicknames)+"')" if full else "nickname LIKE '" + "%' OR nickname LIKE '".join(nicknames)+"%'"
				sql_or.append(nickname_where)
			where=" WHERE (" + " OR ".join(sql_or) + ") AND" if sql_or and subject else " WHERE " + " OR ".join(sql_or)
			if subject:where=where+" subject='"+subject+"'" if full else where+" subject LIKE '"+subject+"%'"
		print('SELECT '+fileds+' FROM phone_book'+where+';')
		for row in self.db.get_data_sql('SELECT '+fileds+' FROM phone_book'+where+';'):
			print(":".join(map(str,row)))
	def edit_phonebook(self, id, phone=None, nickname=None, subject=None, description=None, update_date=False):
		sql_set=[]
		if phone: sql_set.append("phone_number='"+phone+"'")
		if nickname: sql_set.append("nickname='"+nickname+"'")
		if subject: sql_set.append("subject='"+subject+"'")
		if description: sql_set.append("description='"+description+"'")
		if update_date:
			date=datetime.datetime.today()
			sql_set.append("date='"+str(dates.HebrewDate.from_pydate(date))+","+date.strftime("%H:%M:%S")+"'")
		self.db.run_sql('UPDATE phone_book SET '+ ",".join(sql_set) + ' WHERE id=' + str(id) + ';')
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
	del_phonebook_parser.add_argument('-n','--nickname', help="subject and nickname", action='store', nargs=2)
	del_phonebook_parser.set_defaults(action="del")
	add_phonebook_parser = phonebook_subparsers.add_parser('add', help='add new nickname to phonebook')
	add_phonebook_parser.add_argument('nickname', help="nickname to add", action='store')
	add_phonebook_parser.add_argument('phone', help="phone to add", action='store')
	add_phonebook_parser.add_argument('-s','--subject', help="add subject field", action='store')
	add_phonebook_parser.add_argument('-d','--description',help="add description field", action='store')
	add_phonebook_parser.set_defaults(action="add")
	edit_phonebook_parser = phonebook_subparsers.add_parser('edit', help='edit phonebook')
	edit_phonebook_parser.add_argument('id', help="row id for edit", action='store', type=int)
	edit_phonebook_parser.add_argument('-p','--phone', help="edit phone", action='store')
	edit_phonebook_parser.add_argument('-n','--nickname', help="edit nickname", action='store')
	edit_phonebook_parser.add_argument('-s','--subject', help="edit subject", action='store')
	edit_phonebook_parser.add_argument('-d','--description',help="edit description", action='store')
	edit_phonebook_parser.add_argument('-t','--time',help="update date field", action='store_true')
	edit_phonebook_parser.set_defaults(action="edit")
	show_phonebook_parser = phonebook_subparsers.add_parser('show', help='show phonebook')
	show_phonebook_parser.add_argument('-i','--id', help="show id in phonebook",  default=[], dest='ids', action='append', type=int)
	show_phonebook_parser.add_argument('-d','--description',help="show description field", action='store_true')
	show_phonebook_parser.add_argument('-t','--time',help="show update time field", action='store_true')
	show_phonebook_parser.add_argument('-p','--phone', help="show phonebook with phones", default=[], dest='phones', action='append')
	show_phonebook_parser.add_argument('-n','--nickname', help="show phonebook with names", default=[], dest='nicknames', action='append')
	show_phonebook_parser.add_argument('-s','--subject', help="show subject that start with the pattern", action='store')
	show_phonebook_parser.add_argument('-f','--full', help="show only full pattern", action='store_true')
	show_phonebook_parser.set_defaults(action="show")
	phonebook_parser.set_defaults(cmd="phonebook")
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
	if args.cmd and args.cmd == "phonebook" and args.action == "edit" and not (args.phone or args.nickname or args.subject or args.description or args.time):
                print('miss filed for update')
                send_parser.print_usage()
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
				elif args.nickname:cel_modem.db.run_sql("DELETE FROM phone_book WHERE subject = '" + args.nickname[0] + "' and nickname ='"+args.nickname[1]+"' ;")
			elif args.action == 'add':
				date=datetime.datetime.today()
				prefix="INSERT INTO phone_book (date, phone_number, nickname"
				suffix=") VALUES('"+str(dates.HebrewDate.from_pydate(date))+","+date.strftime("%H:%M:%S")+"','"+args.phone+"','"+args.nickname+"'"
				if args.subject:
					prefix=prefix+",subject"
					suffix=suffix+",'"+args.subject+"'"
				if args.description:
					prefix=prefix+",description"
					suffix=suffix+",'"+args.description+"'"
				cel_modem.db.run_sql(prefix+suffix+");")
			elif args.action == 'show':cel_modem.show_phonebook(args.full,args.ids,args.phones,args.nicknames,args.subject,args.description,args.time)
			elif args.action == 'edit':cel_modem.edit_phonebook(args.id, args.phone, args.nickname, args.subject, args.description, args.time)
			else:print("error:bad cmd-"+args.action)
		else:print("error:bad cmd-"+args.cmd)
	if args.quit:cel_modem.quit_modem()
