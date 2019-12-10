#!/usr/bin/python3
from enum import Enum
import os
import led_handler
import argparse
import utils.sqlite_helper
class PMError(Exception):
        def __init__(self, msg):
                self.msg = msg
        def __str__(self):
                return self.msg
class FeatureName(Enum):
	LCD_OFF=0
	LCD_BLANK=1
	PHY_CPCAP_USB=2
	ATMEL_MXT_TS=3
	OMAP2430=4
	IDLE_USB=5
class PM:
	def __init__(self):
		self.leds=led_handler.Leds()
		self.db=utils.sqlite_helper.SqliteHelper('/root/.droid4/hardware.db')
		self.pm_enable=[]
	def out_from_idle(self):
		if FeatureName.LCD_OFF.value in self.pm_enable:self.leds.set_leds(led_handler.LedName.LCD,led_handler.LedAction.TURN_ON)
		if FeatureName.LCD_BLANK.value in self.pm_enable:
			with open('/sys/devices/platform/omapdrm.0/graphics/fb0/blank', "w") as f:
				f.write("0")
		modprobe=[]
		if FeatureName.PHY_CPCAP_USB.value in self.pm_enable:modprobe.append('phy_cpcap_usb')
		if FeatureName.ATMEL_MXT_TS.value in self.pm_enable:modprobe.append('atmel_mxt_ts')
		if FeatureName.OMAP2430.value in self.pm_enable:modprobe.append('omap2430')
		os.system('modprobe -a '+' '.join(modprobe))
	def get_into_idle(self):
		self.pm_enable=self.db.get_list_sql("SELECT feature_id from pm WHERE enable='y'")
		if FeatureName.LCD_OFF.value in self.pm_enable:self.leds.set_leds(led_handler.LedName.LCD,led_handler.LedAction.TURN_OFF)
		if FeatureName.LCD_BLANK.value in self.pm_enable:
			with open('/sys/devices/platform/omapdrm.0/graphics/fb0/blank', "w") as f:
				f.write("1")
		rmmod=[]
		if FeatureName.PHY_CPCAP_USB.value in self.pm_enable:rmmod.append('phy_cpcap_usb')
		if FeatureName.ATMEL_MXT_TS.value in self.pm_enable:rmmod.append('atmel_mxt_ts')
		if FeatureName.OMAP2430.value in self.pm_enable:rmmod.append('omap2430')
		os.system('rmmod '+ '; rmmod '.join(rmmod))
		if FeatureName.IDLE_USB.value in self.pm_enable:
			os.system('qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode=low-power')
			os.system('qmicli -d /dev/cdc-wdm0 --dms-set-operating-mode=online')
			with open('/sys/devices/platform/omapdrm.0/graphics/fb0/blank', "w") as dev:
				dev.write("AT+CFUN=1\r\n")
	def set_features(self, features, enable=True):
		value='y' if enable else 'n'
		self.db.run_sql("UPDATE pm SET enable='" + value + "' WHERE feature_id IN ("+",".join([str(feature.value) for feature in features])+");")
	def list_features(self,features, enable=None):
		where=""
		if features or enable != None:
			where=" WHERE "
			if enable != None:
				where=where+"enable='y'" if enable else where+"enable='n'"
				if features: where=where+" AND "
			if features:where=where+"feature_id IN ("+",".join([str(feature.value) for feature in features])+")"
		for name,enable in self.db.get_data_sql("SELECT name,enable from pm"+ where +";"):
			print(name+":"+enable)
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='tool for set and get pm features.')
	parser.add_argument('-f','--features', help="features for action", default=[], dest='features', action='store', nargs='*', choices=['lcd_off','lcd_blank','phy_cpcap','atmel_mxt_ts','omap2430','idle_usb'])
	action_parser=parser.add_mutually_exclusive_group()
	action_parser.add_argument('-s','--set', help="set feature enable/disable", dest='action', action='store_const', const='set')
	action_parser.add_argument('-l','--list', help="list feature status", dest='action', action='store_const', const='list')
	status_parser=parser.add_mutually_exclusive_group()
	status_parser.add_argument('-e','--enable', help="feature enable", dest='status', default=None, action='store_true')
	status_parser.add_argument('-d','--disable', help="feature disable", dest='status', action='store_false')
	args = parser.parse_args()
#	print(args)
	if not args.action:
		print('miss action:--set/--list')
		parser.print_usage()
		exit(-1)
	pm=PM()
	features = [FeatureName(id) for id in pm.db.get_list_sql("SELECT feature_id from pm WHERE name IN ('"+"','".join(args.features)+"');")] if args.features else [] 
	if args.action == 'set':pm.set_features(features, args.status)
	elif args.action == 'list':pm.list_features(features, args.status)
	else : raise PMError("bad action:"+str(args.action))
