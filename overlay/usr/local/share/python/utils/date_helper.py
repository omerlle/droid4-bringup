#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @author: omerlle (omer levin; omerlle@gmail.com)
# Copyright 2020 omer levin

import datetime
from enum import Enum
class DateError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg
class DateStringFormat(Enum):
	DB=1
	FILENAME=2
def date_to_string(now=None,format=DateStringFormat.DB):
	if not now:now=datetime.datetime.today()
	if format==DateStringFormat.DB:string=now.strftime("%Y-%m-%d %H:%M:%S")
	elif format==DateStringFormat.FILENAME:string=now.strftime("%Y-%m-%d-%H-%M-%S")
	else: DateError('bad format:"'+str(format)+"'")
	return string
