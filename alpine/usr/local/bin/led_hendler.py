#!/usr/bin/python3
class Leds:
	class LedsError(Exception):
		def __init__(self, msg):
			self.msg = msg
		def __str__(self):
			return self.msg
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
		print(value)
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
