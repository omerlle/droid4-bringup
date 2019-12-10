#!/usr/bin/python
import socket
import select
import sys
import os
import traceback
import logging
import threading
import software.modem_helpers as helpers
import software.mamagers_client as clients
from config import app_config
identifier=bytes([255,21])
class ModemServer:
	def __init__(self):
#		logging.debug("init")
		if not os.path.exists(app_config.TMP_PATH):os.mkdir(app_config.TMP_PATH)
		try:
   			os.unlink(app_config.SERVER_ADDRESS)
		except OSError:
    			if os.path.exists(app_config.SERVER_ADDRESS):raise
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.poll=select.poll()
		self.pipe_read, self.pipe_write = os.pipe()
		self.poll.register(self.pipe_read,select.POLLIN)
		self.poll.register(self.sock,select.POLLIN)
		self.msgs={}
		self.stop=False
		self.connections={}
		self.worker=threading.Thread(name="server_worker",target=self.run)
		self.manager_client=clients.ManagerClient()
		self.sms_client=clients.SmsClient()
		self.modem_client=clients.ModemClient()
	def close_connection(self,fd):
		connection = self.connections.pop(fd)
		self.msgs.pop(fd,None)
		self.poll.unregister(fd)
		connection.close()
	def start_thread(self):
#		logging.debug("start_thread")
		self.sock.bind(app_config.SERVER_ADDRESS)
		self.sock.listen(5)
		self.worker.setDaemon(True)
		self.worker.start()
	def stop_thread(self):
		os.write(self.pipe_write,b's')
	def got_msg(self,fd,msg):
		logging.debug("got msg:".encode("utf8")+msg)
#		logging.debug(msg.decode())
		if msg==b'stop':
			logging.debug("get stop")
			self.manager_client.client_command(fd,msg.decode())
		elif msg.startswith(b'send\n'):
#			logging.debug("get:"+str(msg[5:]))
			self.sms_client.send_msg(msg[5:])
		elif msg.startswith(b'phone '):self.modem_client.do_cmd(msg[6:].decode())
		else:raise helpers.ModemError("unknown msg:"+str(msg))
	def run(self):
#		logging.debug("run..")
		while not self.stop:
			try:
				events=self.poll.poll(-1)
				for fd,event in events:
					if fd == self.sock.fileno():
						if event == select.POLLIN:
							connection,_ = self.sock.accept()
							self.connections[connection.fileno()]=connection #TODO:map of connections for close open
							self.poll.register(connection,select.POLLIN|select.POLLHUP)
						else: raise helpers.ModemError("error"+str(event))
					elif fd == self.pipe_read:
						if event == select.POLLIN:
							data=os.read(self.pipe_read,1)
							if data==b's':
								self.stop = True
							else: raise helpers.ModemError("bad sighn:"+str(data))
						else: raise helpers.ModemError("error"+str(event))
					else:
						if event & select.POLLHUP == select.POLLHUP:self.close_connection(fd)
						elif event & select.POLLIN == select.POLLIN:self.recv_msg(fd)
						else:raise helpers.ModemError("error"+str(event))
#			except helpers.ModemError as e:
			except Exception as e:
				logging.error(traceback.format_exc())
		keys=[key for key in self.connections]
		for key in keys:
			self.close_connection(key)
		self.sock.close()
		self.poll.unregister(self.pipe_read)
		os.close(self.pipe_read)
		os.close(self.pipe_write)
#		logging.debug("stoped")
	def recv_msg(self,fd):
		ans = None
		connection=self.connections[fd]
		header, size_header, size, msg = self.msgs[fd] if fd in self.msgs else [False, -1,-1,b'']
		data = ""
		try:
			data = connection.recv(1024)
		except Exception as e:
			self.close_connection(fd)	
		logging.debug(data)
		msg+=data
		msg_len=len(msg)
		stop=False
		while not stop:
			while not header and msg_len > 1:
				if msg[:2]==identifier:header=True
				else:
					msg=msg[1:]
					msg_len -= 1
			#if header still False msg_len<2
			if not header or msg_len <= 2:stop=True
			if not stop and size_header == -1:size_header=msg[2]
			if msg_len <= 3+size_header:stop=True
			if not stop and size == -1:
				prefix_len=3+size_header
				size=int.from_bytes(msg[3:prefix_len], byteorder='big')
				msg=msg[prefix_len:]
				msg_len -= prefix_len
			if msg_len < size:stop=True
			if not stop:
					self.got_msg(fd,msg[:size])
					header, size_header, size, msg =  [False, -1,-1,msg[size:]]
		self.msgs[fd]=[header, size_header, size, msg]
	def send_msg(self,fd,msg):
		connection=self.connections[fd]
		try:
			connection.sendall(msg)
		finally:
			self.close_connection(fd)
	def close(self):
		self.worker.join()
		logging.debug("closed")
	def __del__(self):
		self.close()
