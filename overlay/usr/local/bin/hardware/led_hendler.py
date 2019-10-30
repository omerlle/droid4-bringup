#!/usr/bin/python3

import sys
class LedsError(Exception):							
	def __init__(self, msg):						   
		self.msg = msg					  
	def __str__(self):					      
		return self.msg 
class Leds:
	def __init__(self):
		self.leds={'lcd':"/sys/class/leds/lm3532::backlight/brightness"}
		self.default_brightness={'lcd':200}#TODO:change to sqlite
	def set_leds(self,name,action,value=None,set_default=False):
		if action=="turn off" or action=="set":
			led=open(self.leds[name],"w")
			if action=="turn off":value=0
		else:
			led=open(self.leds[name],"r+")
			current=int(led.read())
			led.seek(0)
			if action=="increase":value=value+current
			elif action=="decrease":value=max(1,current-value)
			elif action=="turn on":
				if current>0:
					led.close()
					return
				value=self.get_default(name)
			else:raise LedsError("unknown action:"+action)
		if value:value=max(0,min(255,value))
		led.write(str(value))
		led.close()
		if set_default: self.set_default(name,value)
#		print(value)
		return

	def get_current(self,name):
		led=open(self.leds[name])
		current=int(led.read())		     
		led.close()				 
		return current			      
	def is_on(self,name):			       
		return self.get_current(name) != 0
	def get_default(self,name):	       
		return self.default_brightness[name]
	def set_default(self,name,value):	   
		self.default_brightness[name]=max(1,min(255,value))
if __name__ == '__main__':
	params_num=len(sys.argv)
	if params_num <3:
		print("Usage:led_hendler.py action name [arg]")
		exit(1) 
	action=sys.argv[1]
	leds=Leds()
	if action == 'is_on':print(leds.is_on(sys.argv[2]))
	elif action == 'get brightness':print(leds.get_current(sys.argv[2]))
	elif action == 'get default':print(leds.get_default(sys.argv[2]))
	else:
		if params_num <4:				       
			print("need to enter value")		  
			exit(1)	
		else: 
			if action == 'set default':leds.set_default(sys.argv[2],int(sys.argv[3]))
			elif action == 'set brightness':
				if params_num == 4: leds.set_leds(sys.argv[2],sys.argv[3])
				elif params_num == 5: leds.set_leds(sys.argv[2],sys.argv[3],int(sys.argv[4]))
				else: leds.set_leds(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
			else:
				print("bad usage:action not exist")
				exit(1)
