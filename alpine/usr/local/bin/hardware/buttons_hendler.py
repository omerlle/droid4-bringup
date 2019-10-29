#!/usr/bin/python3
import select
import evdev
import led_hendler
class ButtonsError(Exception):
	def __init__(self, msg):
		self.msg = msg
	def __str__(self):
		return self.msg
if __name__ == '__main__':
	leds=led_hendler.Leds()
	devices = [evdev.InputDevice(path) for path in evdev.list_devices()] # if not Atmel maXTouch Touchscreen
#       print(device.path, device.name, device.phys)
	devices = {dev.fd: dev for dev in devices}
	poll=select.poll()
	for key in devices.keys():
		poll.register(key,select.POLLIN)
	while True:
		events=poll.poll(-1)
		for fd,event in events:
			if event == select.POLLIN:
				for key in devices[fd].read():
					if key.type == evdev.ecodes.EV_KEY:
						if key.value == 0:#up  hold=2 down=1
							if key.code == evdev.ecodes.KEY_POWER:
								leds.set_leds('lcd','turn off') if leds.is_on('lcd') else leds.set_leds('lcd','turn on')
							elif key.code == evdev.ecodes.KEY_VOLUMEUP:
								if leds.is_on('lcd'): leds.set_leds('lcd',"increase",25,True)
							elif key.code == evdev.ecodes.KEY_VOLUMEDOWN:
								if leds.is_on('lcd'): leds.set_leds('lcd',"decrease",25,True)
#					       else:
#				       print(evdev.categorize(event))
#					       print(event)
#			       else:
			else: raise ButtonsError("bad poll event"+str(event))

