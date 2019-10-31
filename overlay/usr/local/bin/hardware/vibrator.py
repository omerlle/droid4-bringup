#!/usr/bin/python3
import evdev
import struct
import os
import sys
from time import sleep
if __name__ == '__main__':
	duration_ms = 150
	find=False
	if len(sys.argv)>1 : duration_ms = int(sys.argv[1])
	for name in evdev.list_devices():
		dev = evdev.InputDevice(name)
		if evdev.ecodes.EV_FF in dev.capabilities() and dev.name=="pwm-vibrator":
			find=True
			break
	if find:
		effect_type = evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(strong_magnitude=0x0000, weak_magnitude=0xffff))
		effect = evdev.ff.Effect(
evdev.ecodes.FF_RUMBLE, -1, 0, evdev.ff.Trigger(0, 0), evdev.ff.Replay(duration_ms, 0), effect_type
)
		effect_id = dev.upload_effect(effect)

		FORMAT = 'llHHI'
		event =struct.pack(FORMAT, 0,0,evdev.ecodes.EV_FF, 0,1)
		os.write(dev.fileno(), event)
		sleep(duration_ms/1000.0)
		dev.erase_effect(effect_id)
	else:
		print("not found pwm-vibrator")
