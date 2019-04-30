#!/usr/bin/python
# -*- coding: utf-8 -*-
import evdev
import struct
import os
import select
import threading
import logging
from time import sleep
from subprocess import call
CHUNK=1024
MODEM='/dev/motmdm1'
CALL_LIST_FILENAME='/tmp/call_list'
SIGNALSTRENGTH_FILENAME='/tmp/signal_strength'
stop=True
def pwm_vibrator():
	logging.basicConfig(filename=CALL_LIST_FILENAME,level=logging.INFO,format='[%(asctime)s]|%(message)s',)
	logging.getLogger('call_list')
	for name in evdev.list_devices():
		dev = evdev.InputDevice(name)
		if evdev.ecodes.EV_FF in dev.capabilities() and dev.name=="pwm-vibrator":
			find=True
			break
	if not find:
		logging.error("not found pwm-vibrator")
		return
	duration_ms = 150
	effect_type = evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(strong_magnitude=0x0000, weak_magnitude=0xffff))
	effect = evdev.ff.Effect(
evdev.ecodes.FF_RUMBLE, -1, 0, evdev.ff.Trigger(0, 0), evdev.ff.Replay(duration_ms, 0), effect_type
)
	effect_id = dev.upload_effect(effect)

	FORMAT = 'llHHI'
	event =struct.pack(FORMAT, 0,0,evdev.ecodes.EV_FF, 0,1)
	while True:
		e.wait()
		print("start vibrate..")
		while not stop:
			os.write(dev.fileno(), event)
			sleep(2)
	dev.erase_effect(effect_id)	
if __name__ == '__main__':
	e = threading.Event()
	vibrate =threading.Thread(name="vibraty",target=pwm_vibrator)
	vibrate.setDaemon(True)
	vibrate.start()
	modem_read = open(MODEM,"r")
	pollerObject = select.poll() 
	pollerObject.register(modem_read, select.POLLIN)
	while(True):
	    fdVsEvent = pollerObject.poll(10000)
	    for descriptor, Event in fdVsEvent:
        	#print("Got an incoming connection request"+str(Event))
		line = modem_read.readline()
		print("Got line:"+line)
		if line.startswith("~+RSSI="):
			with open(SIGNALSTRENGTH_FILENAME, "a") as dev:
				dev.write(line)
		if line.startswith("~+CLIP=\""):
			number = line.split('"', 2)[1]
			#print('get call:"'+ number+'"')
			logging.info(number)			
			stop=False
			e.set()
		if line.startswith("A:OK"):
			if e.isSet(): print('error')
			stop=True
			e.clear()
		if line.startswith("~+CIEV=1,0,0"):
			stop=True
			e.clear()
		if line.startswith("D:OK"):
			pass
