# -*- coding: utf-8 -*-
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
	def __init__(self,name):
		self.connection = sqlite3.connect(name)
		self.connection.execute("PRAGMA foreign_keys = 1")
		self.connection.commit()
	def __del__(self):
		self.connection.close()
		self.connection = None
	def get_data_sql(self,sql):
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
