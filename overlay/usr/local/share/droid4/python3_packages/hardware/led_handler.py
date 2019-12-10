#!/usr/bin/python3

from enum import Enum
import utils.sqlite_helper
import argparse
import sys

import sqlite3

import utils.sqlite_helper

__author__ = "omer levin"
__email__ = "omerlle@gmail.com"

class LedsError(Exception):							
	def __init__(self, msg):						   
		self.msg = msg					  
	def __str__(self):					      
		return self.msg 
class LedName(Enum):
	LCD=0
	RED=1
	BLUE=2
	GREEN=3
	KEYBOARD=4
	BUTTONS=5
class LedAction(Enum):
	SET=0
	TURN_OFF=1
	TURN_ON=2
	INCREASE=3
	DECREASE=4
class Leds:
	def __init__(self):
		self.db=utils.sqlite_helper.SqliteHelper('/root/.droid4/hardware.db')
	def set_leds(self,id,action,value=None,set_default=False):
		filename=self.get_filename(id)
		if action==LedAction.TURN_OFF or action==LedAction.SET:
			led=open(filename,"w")
			if action==LedAction.TURN_OFF:value=0
		else:
			led=open(filename,"r+")
			current=int(led.read())
			led.seek(0)
			if action==LedAction.INCREASE:value=value+current
			elif action==LedAction.DECREASE:value=max(1,current-value)
			elif action==LedAction.TURN_ON:
				if current>0:
					led.close()
					return
				value=self.get_default(id)
			else:raise LedsError("unknown action:"+str(action))
		if value:value=max(0,min(255,value))
		led.write(str(value))
		led.close()
		if set_default: self.set_default(name,value)
#		print(value)
		return
	def get_filename(self,id):
		return "/sys/class/leds/"+self.db.get_value_sql('SELECT sys_name FROM leds WHERE id='+str(id.value)+';')+"/brightness"
	def get_current(self,id):
		led=open(self.get_filename(id))
		current=int(led.read())		     
		led.close()				 
		return current			      
	def is_on(self,id):			       
		return self.get_current(id) != 0
	def get_default(self,id):
		return self.db.get_value_sql("SELECT default_value from leds WHERE id = "+str(id.value)+";")
	def set_default(self,id,value):
		return self.db.run_sql('UPDATE leds SET default_value='+value+' WHERE id = '+str(id.value)+';')
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='tool for hardware leds manipulation.')
	set_led = parser.add_mutually_exclusive_group()
	set_led.add_argument('-o','--on', help="turn on/off", dest='set_on', action='store_true')
	set_led.add_argument('-f','--off', help="turn on/off", dest='set_on', action='store_false')
	set_led.add_argument('-s','--set', help="the value for set", action='store', type=int)
	parser.add_argument('-d','--set_default', help="set the default for led", action='store', type=int)
	parser.add_argument('-g','--get', help="the value you what to get", action='store', choices=['on', 'default','value'])
	parser.add_argument('names', help="led name for manipulation", nargs='+', action='store',choices=['lcd', 'red','blue','green','keyboard','buttons'])
	args = parser.parse_args()
#       print(args)
	leds=Leds()
	if args.set_default:
		for name in args.names:
			leds.set_default(LedName(leds.db.get_value_sql("SELECT id from leds WHERE name = '"+name+"';")),args.set_default)
	if args.set or args.set_on != None:
		if args.set:
			action=LedAction.SET
			value=args.set
		else:
			value=None
			action=LedAction.TURN_ON if args.set_on else LedAction.TURN_OFF
		for name in args.names:
			leds.set_leds(LedName(leds.db.get_value_sql("SELECT id from leds WHERE name = '"+name+"';")), action, value)
	if args.get:
		if args.get=='on':get=leds.is_on
		elif args.get=='default':get=leds.get_default
		elif args.get=='value':get=leds.get_current
		else:raise LedsError("bad get value:"+args.get)
		for name in args.names:
			print(name + ":" + get(LedName(leds.db.get_value_sql("SELECT id from leds WHERE name = '"+name+"';"))))
