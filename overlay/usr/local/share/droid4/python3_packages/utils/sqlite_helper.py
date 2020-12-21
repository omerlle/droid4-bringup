#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import logging
import sqlite3
import threading
lock = threading.RLock()
class SqliteHelperError(Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg
class SqliteHelper:
	def __init__(self,name,connect=True):
		self.name=name
		self.connection = None
		if connect:self.connect()
	def connect(self):
		self.connection = sqlite3.connect(self.name)
		self.connection.execute("PRAGMA foreign_keys = 1")
		self.connection.commit()
	def __del__(self):
		if self.connection:self.connection.close()
		self.connection = None
	def get_data_sql(self,sql):
		if not self.connection:self.connect()
		logging.debug(sql)
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
		if len(ans)> 1 or (ans and len(ans[0])> 1): raise SqliteHelperError("error: get more then one value:"+ans + "for sql:"+sql)
		value = None if not ans else ans[0][0]
		if not null_valid and value == None : raise SqliteHelperError("error: didn't get value("+str(ans)+") for sql:"+sql)
		return value
	def get_list_sql(self,sql,encode=False):
		if encode: return [ value[0].encode("utf8") for value in self.get_data_sql(sql)]
		return [ value[0] for value in self.get_data_sql(sql)]
	def run_sql(self,sql,args=None,many=False):
		if not self.connection:self.connect()
		logging.debug(sql)
		lock.acquire()
		try:
			if args:
				if not many:
					self.connection.cursor().execute(sql,args)
				else:
					self.connection.cursor().executemany(sql,args)
			else: self.connection.cursor().execute(sql)
			self.connection.commit()
		except Exception:
			self.connection.commit()
			lock.release()
			raise
		lock.release()
	def insert_row_and_get_id(self,sql_insert,args):
		if not self.connection:self.connect()
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
