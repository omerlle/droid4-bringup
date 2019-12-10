#!/usr/bin/python3

import os
import select
import traceback

import evdev

import pm_handler
import modem.client as modem_client

class ButtonsError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg
if __name__ == '__main__':
	pm=pm_handler.PM()
	modem=modem_client.Client()
	symbols=False
	idle=False
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
	devices = {dev.fd: dev for dev in devices if not dev.name.startswith("Atmel maXTouch Touchscreen")}
	poll=select.poll()
	for key in devices.keys():
		poll.register(key,select.POLLIN)
	while True:
		try:
			events=poll.poll(-1)
			for fd,event in events:
				if event == select.POLLIN:
					for key in devices[fd].read():
						if key.type == evdev.ecodes.EV_KEY:
							if key.value == 0:#up  hold=2 down=1
								if key.code == evdev.ecodes.KEY_POWER:
									if idle:pm.out_from_idle()
									else:pm.get_into_idle()
									idle=not idle
								elif key.code == evdev.ecodes.KEY_VOLUMEUP:
									modem.answer()	
#									if leds.is_on(led_handler.LedName.LCD): leds.set_leds(led_handler.LedName.LCD,led_handler.LedAction.INCREASE,25,True)
								elif key.code == evdev.ecodes.KEY_VOLUMEDOWN:
									modem.hangup()
#									if leds.is_on(led_handler.LedName.LCD): leds.set_leds(led_handler.LedName.LCD,led_handler.LedAction.DECREASE,25,True)
								elif key.code == evdev.ecodes.KEY_OK:
									if symbols==True:
										os.system('loadkeys us')
									else:
										os.system('loadkeys /usr/local/share/fonts/symbols -C /dev/tty1')
									symbols = not symbols
				elif event & select.POLLHUP == select.POLLHUP:self.poll.unregister(fd)
				else: raise ButtonsError("bad poll event"+str(event))
		except Exception as e:
			print(traceback.format_exc())
	print('exit')
