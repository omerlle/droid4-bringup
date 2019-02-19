#!/usr/bin/python
# -*- coding: utf-8 -*-

import wave
import alsaaudio
import select
import threading
import logging
from subprocess import call
CHUNK=1024
MODEM='/dev/motmdm1'
CALL_LIST_FILENAME='/tmp/call_list'
SIGNALSTRENGTH_FILENAME='/tmp/signal_strength'
INCOMING_CALL_WAVE='/usr/share/sounds/modem/incomming_call_sound.wav'
stop=True

def play_wave_to_pcm(e):
	logging.basicConfig(filename=CALL_LIST_FILENAME,level=logging.INFO,format='[%(asctime)s]|%(message)s',)
	logging.getLogger('call_list')
	wf = wave.open(INCOMING_CALL_WAVE, 'rb')
	channels=wf.getnchannels()
	rate=wf.getframerate()
	wave_format=alsaaudio.PCM_FORMAT_U8 #PCM_FORMAT_FLOAT_LE
	data=[]	
	while True:
		chunk=wf.readframes(CHUNK)
		if chunk == '': break
		data.append(chunk)
	wf.close()
	length=len(data)
	while True:
		e.wait()
		print("start play..")
		i=0
		sound_out = alsaaudio.PCM()  # open default sound output
		sound_out.setchannels(channels)  # use only one channel of audio (aka mono)
		sound_out.setrate(rate)  # how many samples per second
		sound_out.setformat(wave_format)  # sample format
		while not stop:
			sound_out.write(data[i])
			i=(i+1)%length
		sound_out = None
		#mixaer=alsaaudio.Mixer(control='Speaker Right')
		
if __name__ == '__main__':
	e = threading.Event()
	play_wave =threading.Thread(name="playing",target=play_wave_to_pcm,args=(e,))
	play_wave.setDaemon(True)
	play_wave.start()
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
			call(["amixer", "sset", "Speaker Right", "Voice"])
		if line.startswith("~+CIEV=1,0,0"):
			stop=True
			e.clear()
			call(["amixer", "sset", "Speaker Right", "HiFi"])
		if line.startswith("D:OK"):
			call(["amixer", "sset", "Speaker Right", "Voice"])	
