#!/usr/bin/python
# -*- coding: utf-8 -*-
import modem.config.app_config as config
import modem.software.modem_helpers as helpers
import logging
import sqlite3
import threading
lock = threading.RLock()
class sms_db:
	def __init__(self):#, arg):
		self.connection = sqlite3.connect(config.DATABASE_FILENAME)
		self.connection.execute("PRAGMA foreign_keys = 1")
		self.connection.commit()
	def __del__(self):
		self.connection.close()
		self.connection = None
	def get_data_sql(self,sql):
		lock.acquire()
		try:
			cursor = self.connection.cursor()
			cursor.execute(sql)
			ans = cursor.fetchall()
		except Exception:
			lock.release()
			raise
		lock.release()
		return ans
	def get_value_sql(self,sql,null_valid=False):
		ans = self.get_data_sql(sql)
		if len(ans)> 1 or (ans and len(ans[0])> 1): raise helpers.ModemError("error: get more then one value:"+ans + "for sql:"+sql)
		value = None if not ans else ans[0][0]
		if not null_valid and value == None : raise helpers.ModemError("error: didn't get value("+str(ans)+") for sql:"+sql)
#		logging.debug("from:" + sql)
#		logging.debug(value)
		return value
	def get_list_sql(self,sql,encode=False):
		if encode: return [ value[0].encode("utf8") for value in self.get_data_sql(sql)]
		return [ value[0] for value in self.get_data_sql(sql)]
	def run_sql(self,sql,args=None):
		logging.debug(sql)
#		logging.debug(args)
		lock.acquire()
		try:
			if args:self.connection.cursor().execute(sql,args)
			else: self.connection.cursor().execute(sql)
			self.connection.commit()
		except Exception:
			self.connection.commit()
			lock.release()
			raise
		lock.release()
	def insert_row_and_get_id(self,sql_insert,args):
#		logging.debug(sql_insert)
#		logging.debug(args)
		lock.acquire()
		id=-1
		try:
			cursor=self.connection.cursor()
			cursor.execute(sql_insert,args)
			id=cursor.lastrowid
			self.connection.commit()
			#id=cursor.lastrowid
		except Exception:
			self.connection.commit()
			lock.release()
			raise
		lock.release()
		return id
#	def set_voice_call_status(self,status):
#		self.run_sql("UPDATE voice_call_status SET status = "+str(status)+";")
#	def get_voice_call_status(self,status):
#		self.run_sql("SELECT status voice_call_status SET status = "+str(status)+";")
	def get_and_set_reference_number(self,phone,long_reference_number=True):#16-bit
		column_name='long_reference_number' if long_reference_number else 'short_reference_number'
		max_number=65535 if long_reference_number else 255
		self.run_sql("INSERT OR IGNORE INTO phones (phone) VALUES('"+phone+"');")
		reference_number=self.get_value_sql("SELECT "+column_name+" FROM phones WHERE phone ='" + phone +"';")
		self.run_sql("UPDATE phones SET "+column_name+" = '"+str(reference_number+1 if reference_number<max_number else 0)+"' WHERE phone='"+phone+"';")
		return reference_number
