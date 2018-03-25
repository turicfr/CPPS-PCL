import os
import sys
import socket
import hashlib
import re
import json
import threading
import Queue
import logging
from penguin import Penguin
from aes import AES

class _Handler(object):
	def __init__(self, handlers, predicate):
		self._handlers = handlers
		self._predicate = predicate

	def handle(self, packet):
		if self._predicate is None or self._predicate(packet):
			self.inner_handle(packet)
			return True
		return False

class _CallbackHandler(_Handler):
	def __init__(self, handlers, predicate, callback):
		super(_CallbackHandler, self).__init__(handlers, predicate)
		self._callback = callback

	def inner_handle(self, packet):
		if self._callback is not None:
			self._callback(packet)

	def __del__(self):
		self._handlers.remove(self)

class _OneTimeHandler(_Handler):
	def __init__(self, handlers, cmd, inner_predicate, timeout):
		if cmd is None:
			predicate = inner_predicate
		elif inner_predicate is None:
			predicate = lambda p: p[2] == cmd
		else:
			predicate = lambda p: p[2] == cmd and inner_predicate(p)
		super(_OneTimeHandler, self).__init__(handlers, predicate)
		self._cmd = cmd
		self._timeout = timeout
		self._queue = Queue.Queue(1)

	def inner_handle(self, packet):
		self._queue.put(packet)
		self._handlers.remove(self)

	@property
	def packet(self):
		try:
			return self._queue.get(timeout=self._timeout)
		except Queue.Empty:
			self._handlers.remove(self)
			return None

class ClientError(Exception):
	def __init__(self, message, code=0):
		super(ClientError, self).__init__(message)
		self.code = code			

class Client(object):
	def __init__(self, login_ip, login_port, game_ip, game_port, magic=None, single_quotes=False, logger=None):
		self._login_ip = login_ip
		self._login_port = login_port
		self._game_ip = game_ip
		self._game_port = game_port
		if logger is None:
			logger = logging.getLogger()
			logger.setLevel(logging.NOTSET)
			handler = logging.StreamHandler(sys.stdout)
			logger.addHandler(handler)
		self._logger = logger
		self._magic = "Y(02.>'H}t\":E1" if magic is None else magic
		self._single_quotes = single_quotes
		self._walk_internal_room_id = False

		self._connected = False
		self._buffer = ""
		self._handlers = {}
		self._nexts = []
		self._heartbeat_timer = None
		self._internal_room_id = -1
		self._id = -1
		self._coins = -1
		self._room = -1
		self._penguins = {}
		self._follow = None

	def __iter__(self):
		return self

	def __exit__(self):
		self.logout()

	@staticmethod
	def _swapped_md5(password, encrypted=False):
		if not encrypted:
			password = hashlib.md5(password).hexdigest()
		password = password[16:32] + password[0:16]
		return password

	def _debug(self, message):
		if self._logger is not None:
			self._logger.debug(message)

	def _info(self, message):
		if self._logger is not None:
			self._logger.info(message)

	def _warning(self, message):
		if self._logger is not None:
			self._logger.warning(message)

	def _error(self, message):
		if self._logger is not None:
			if isinstance(message, list):
				filename = os.path.join(os.path.dirname(__file__), "json/errors.json")
				with open(filename) as file:
					data = json.load(file)
				code = int(message[4])
				message = "Error #{}".format(code)
				if str(code) in data:
					message += ": {}".format(data[str(code)])
			self._logger.error(message)

	def _critical(self, message):
		if self._logger is not None:
			self._logger.critical(message)

	def _send(self, data):
		self._debug("# Send: {}".format(data))
		try:
			self.sock.send(data + chr(0))
			return True
		except socket.error:
			self._critical("Connection lost")
			return False

	def _send_packet(self, ext, cmd, *args):
		packet = "%xt%{}%{}%".format(ext, cmd)
		if args and args[0] is None:
			args = args[1:]
		else:
			packet += str(self._internal_room_id) + "%"
		packet += "".join(str(arg) + "%" for arg in args)
		return self._send(packet)

	def _receive(self):
		data = ""
		try:
			while not chr(0) in self._buffer:
				data += self._buffer
				self._buffer = self.sock.recv(4096)
		except socket.error:
			return None
		i = self._buffer.index(chr(0))
		data += self._buffer[:i]
		self._buffer = self._buffer[i + 1:]
		self._debug("# Receive: {}".format(data))
		return data

	def _receive_packet(self):
		data = self._receive()
		while not data:
			if data is None:
				return None
			data = self._receive()
		if data.startswith("%"):
			packet = data.split('%')
			if packet[2] == "e":
				self._error(packet)
			return packet
		raise ClientError("Invalid packet: {}".format(data))

	def _ver_check(self, ver):
		self._info("Sending 'verChk' request...")
		if self._single_quotes:
			data = "<msg t='sys'><body action='verChk' r='0'><ver v='{}' /></body></msg>".format(ver)
		else:
			data = '<msg t="sys"><body action="verChk" r="0"><ver v="{}"/></body></msg>'.format(ver)
		if not self._send(data):
			return False
		data = self._receive()
		if data is None:
			return False
		if "cross-domain-policy" in data:
			data = self._receive()
			if data is None:
				return False
		if "apiOK" in data:
			self._info("Received 'apiOK' response")
			return True
		if "apiKO" in data:
			self._info("Received 'apiKO' response")
			return False
		raise ClientError("Invalid verChk response: {}".format(data))

	def _rndk(self):
		self._info("Sending rndK request...")
		if self._single_quotes:
			data = "<msg t='sys'><body action='rndK' r='-1'></body></msg>"
		else:
			data = '<msg t="sys"><body action="rndK" r="-1"></body></msg>'
		if not self._send(data):
			return None
		data = self._receive()
		if data is None:
			return None
		if "rndK" in data:
			key = re.search("<k>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/k>", data).group(1)
			self._info("Received key: {}".format(key))
			return key
		raise ClientError("Invalid rndk response: {}".format(data))

	def _login(self, user, password, encrypted, ver):
		self._info("Logging in...")
		if not self._ver_check(ver):
			return None, False
		rndk = self._rndk()
		if rndk is None:
			return None, False
		if self._magic:
			hash = self._swapped_md5(self._swapped_md5(password, encrypted).upper() + rndk + self._magic)
			if rndk == "houdini":
				aes = AES(256, 256)
				hash = aes.encrypt(hash, "67L8CALPPCD4J283WL3JF3T2T32DFGZ8", "ECB")
		else:
			hash = password
		if self._single_quotes:
			data = "<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>".format(user, hash)
		else:
			data = '<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>'.format(user, hash)
		if not self._send(data):
			return None, False
		packet = self._receive_packet()
		if packet is None or packet[2] == "e":
			return packet, False
		while packet[2] != "l":
			packet = self._receive_packet()
			if packet is None or packet[2] == "e":
				return packet, False
		self._info("Logged in")
		return packet, True

	def _join_server(self, user, login_key, confirmation, ver):
		self._info("Joining server...")
		if not self._ver_check(ver):
			return None, False
		rndk = self._rndk()
		if rndk is None:
			return None, False
		hash = self._swapped_md5(login_key + rndk) + login_key
		if confirmation is not None:
			hash += '#' + confirmation
		if self._single_quotes:
			data = "<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>".format(user, hash)
		else:
			data = '<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>'.format(user, hash)
		if not self._send(data):
			return None, False
		packet = self._receive_packet()
		if packet is None or packet[2] == "e":
			return packet, False
		while packet[2] != "l":
			packet = self._receive_packet()
			if packet is None or packet[2] == "e":
				return packet, False
		if not self._send_packet("s", "j#js", self._id, login_key, "en"):
			return None, False
		if confirmation is None:
			while packet[2] != "js":
				packet = self._receive_packet()
				if packet is None or packet[2] == "e":
					return packet, False
		self._info("Joined server")
		return packet, True

	def _lp(self, packet):
		del self._handlers["lp"]
		penguin = Penguin.from_player(packet[4])
		self._penguins[penguin.id] = penguin
		self._coins = int(packet[5])
		safemode = packet[6] == '1'
		# egg_timer = int(packet[7])
		login_time = long(packet[8])
		age = int(packet[9])
		# banned_age = int(packet[10])
		play_time = int(packet[11])
		try:
			member_left = int(packet[12])
		except ValueError:
			member_left = None
		timezone = int(packet[13])
		# opened_playcard = packet[14] == '1'
		# saved_map_category = int(packet[15])
		# status_field = int(packet[16])

		thread = threading.Thread(target=self._heartbeat)
		thread.start()

	def _ap(self, packet):
		penguin = Penguin.from_player(packet[4])
		self._penguins[penguin.id] = penguin

	def _rp(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins.pop(id)
		if self._follow is not None and id == self._follow[0]:
			self._send_packet("s", "b#bf", id)
			packet = self.next("bf")
			if packet is None:
				return
			self.room = int(packet[4])

	def _jr(self, packet):
		internal_room_id = int(packet[3])
		if self._internal_room_id < 0:
			self._internal_room_id = internal_room_id
		elif internal_room_id:
			self._internal_room_id = internal_room_id
		self._room = int(packet[4])
		self._penguins.clear()
		for i in packet[5:-1]:
			penguin = Penguin.from_player(i)
			self._penguins[penguin.id] = penguin

	def _br(self, packet):
		id = int(packet[4])
		name = packet[5]
		self._send_packet("s", "b#ba", id)

	def _upc(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.color = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.color = penguin.color

	def _uph(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.head = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.head = penguin.head

	def _upf(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.face = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.face = penguin.face

	def _upn(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.neck = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.neck = penguin.neck

	def _upb(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.body = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.body = penguin.body

	def _upa(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.hand = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.hand = penguin.hand

	def _upe(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.feet = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.feet = penguin.feet

	def _upl(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.pin = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.pin = penguin.pin

	def _upp(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.background = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.background = penguin.background

	def _sp(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.x = int(packet[5])
			penguin.y = int(packet[6])
			if self._follow is not None and id == self._follow[0]:
				self.walk(penguin.x + self._follow[1], penguin.y + self._follow[2])

	def _sa(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			action = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.action(action)

	def _sf(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			penguin.frame = int(packet[5])
			if self._follow is not None and id == self._follow[0]:
				self.frame = penguin.frame

	def _sb(self, packet):
		id = int(packet[4])
		x = int(packet[5])
		y = int(packet[6])
		if self._follow is not None and id == self._follow[0]:
			self.snowball(x, y)

	def _sm(self, packet):
		id = int(packet[4])
		message = packet[5]
		if self._follow is not None and id == self._follow[0]:
			self.say(message)

	def _ss(self, packet):
		id = int(packet[4])
		message = packet[5]
		if self._follow is not None and id == self._follow[0]:
			self.say(message, True)

	def _sj(self, packet):
		id = int(packet[4])
		joke = int(packet[5])
		if self._follow is not None and id == self._follow[0]:
			self.joke(joke)

	def _se(self, packet):
		id = int(packet[4])
		emote = int(packet[5])
		if self._follow is not None and id == self._follow[0]:
			self.emote(emote)

	def _game(self):
		self.handle("h")
		self.handle("lp", self._lp)
		self.handle("ap", self._ap)
		self.handle("rp", self._rp)
		self.handle("jr", self._jr)
		self.handle("upc", self._upc)
		self.handle("uph", self._uph)
		self.handle("upf", self._upf)
		self.handle("upn", self._upn)
		self.handle("upb", self._upb)
		self.handle("upa", self._upa)
		self.handle("upe", self._upe)
		self.handle("upl", self._upl)
		self.handle("upp", self._upp)
		self.handle("sp", self._sp)
		self.handle("sa", self._sa)
		self.handle("sf", self._sf)
		self.handle("sb", self._sb)
		self.handle("sm", self._sm)
		self.handle("ss", self._ss)
		self.handle("sj", self._sj)
		self.handle("se", self._se)

		try:
			self.walk(0, 0, False)
			self._walk_internal_room_id = False
		except ClientError:
			try:
				self.walk(0, 0, True)
				self._walk_internal_room_id = True
			except ClientError:
				self._warning("Walk method not found")

		while self._connected:
			packet = self._receive_packet()
			if not self._connected:
				break
			if packet is None:
				self.logout()
				break
			cmd = packet[2]
			handled = False
			if cmd in self._handlers:
				for handler in self._handlers[cmd]:
					try:
						if handler.handle(packet):
							handled = True
					except ClientError as e:
						self._error(e.message)
			for handler in self._nexts:
				try:
					if handler.handle(packet):
						handled = True
						break
				except ClientError as e:
					self._error(e.message)
			if not handled:
				self._warning("# Unhandled packet: {}".format('%'.join(packet)))

		if self._heartbeat_timer is not None:
			self._heartbeat_timer.cancel()

	def connect(self, user, password, encrypted=False, ver=153):
		self._info("Connecting to login server at {}:{}...".format(self._login_ip, self._login_port))
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect((self._login_ip, self._login_port))
		except socket.error:
			raise ClientError("Failed to connect to login server at {}:{}".format(self._login_ip, self._login_port))

		packet, ok = self._login(user, password, encrypted, ver)
		if not ok:
			raise ClientError("Failed to log in", 0 if packet is None else int(packet[4]))

		if '|' in packet[4]:
			user = packet[4]
			data = packet[4].split('|')
			self._id = int(data[0])
			# swid = data[1]
			# user = data[2]
			login_key = data[3]
			# ??? = data[4]
			# language_approved = int(data[5])
			# language_rejected = int(data[6])
			# ??? = data[7] == "true"
			# ??? = data[8] == "true"
			# ??? = int(data[9])
			confirmation = packet[5]
			# friends_login_key = packet[6]
			# ??? = packet[7]
			# email = packet[8]
		else:
			self._id = int(packet[4])
			login_key = packet[5]
			confirmation = None

		self._info("Connecting to game server at {}:{}...".format(self._game_ip, self._game_port))
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect((self._game_ip, self._game_port))
		except socket.error:
			raise ClientError("Failed to connect to game server at {}:{}".format(self._game_ip, self._game_port))

		packet, ok = self._join_server(user, login_key, confirmation, ver)
		if not ok:
			raise ClientError("Failed to join server", 0 if packet is None else int(packet[4]))
		
		self._connected = True
		thread = threading.Thread(target=self._game)
		thread.start()

	def handle(self, cmd, callback=None, predicate=None):
		if cmd not in self._handlers or not self._handlers[cmd]:
			self._handlers[cmd] = set()
		handler = _CallbackHandler(self._handlers[cmd], predicate, callback)
		self._handlers[cmd].add(handler)
		return handler

	def next(self, cmd=None, predicate=None, timeout=5):
		handler = _OneTimeHandler(self._nexts, cmd, predicate, timeout)
		self._nexts.append(handler)
		return handler.packet

	@property
	def login_ip(self):
		return self._login_ip

	@property
	def login_port(self):
		return self._login_port

	@property
	def game_ip(self):
		return self._game_ip

	@property
	def game_port(self):
		return self._game_port

	@property
	def logger(self):
		return self._logger

	@property
	def connected(self):
		return self._connected

	@property
	def internal_room_id(self):
		return self._internal_room_id

	@property
	def id(self):
		return self._id

	def get_id(self, name):
		for penguin in self._penguins.values():
			if penguin.name == name:
				return penguin.id
		return 0

	@property
	def name(self):
		return self._penguins[self._id].name

	@property
	def coins(self):
		return self._coins

	@property
	def room(self):
		return self._room

	@room.setter
	def room(self, id, x=0, y=0):
		self._info("Joining room {}...".format(id))
		self._send_packet("s", "j#jr", id, x, y)
		packet = self.next("jr")
		if packet is None:
			raise ClientError("Failed to join room {}".format(id))
		self._info("Joined room {}".format(id))

	@staticmethod
	def get_room_id(name):
		filename = os.path.join(os.path.dirname(__file__), "json/rooms.json")
		with open(filename) as file:
			data = json.load(file)
		for id in data:
			if data[id] == name:
				return int(id)
		return 0

	@staticmethod
	def get_room_name(id):
		filename = os.path.join(os.path.dirname(__file__), "json/rooms.json")
		with open(filename) as file:
			data = json.load(file)
		if str(id) in data:
			return data[str(id)]
		return "Unknown"

	@property
	def igloo(self):
		if self._room > 1000:
			return self._room - 1000

	@igloo.setter
	def igloo(self, id):
		name = self._penguins[id].name if id in self._penguins else "Penguin {}".format(id)
		self._info("Joining {}'s igloo...".format(name))
		self._send_packet("s", "j#jp", None, self._id, int(id) + 1000)
		packet = self.next("jr")
		if packet is None:
			raise ClientError("Failed to join {}'s igloo".format(name))
		self._info("Joined {}'s igloo".format(name))

	@property
	def penguins(self):
		return self._penguins

	@property
	def color(self):
		return self._penguins[self._id].color

	@color.setter
	def color(self, id):
		self._info("Changing color to {}...".format(id))
		self._send_packet("s", "s#upc", id)
		packet = self.next("upc")
		if packet is None:
			raise ClientError("Failed to change color to {}".format(id))
		self._info("Changed color to {}".format(id))

	@property
	def head(self):
		return self._penguins[self._id].head

	@head.setter
	def head(self, id):
		self._info("Changing head item to {}...".format(id))
		self._send_packet("s", "s#uph", id)
		packet = self.next("uph")
		if packet is None:
			raise ClientError("Failed to change head item to {}".format(id))
		self._info("Changed head item to {}".format(id))

	@property
	def face(self):
		return self._penguins[self._id].face

	@face.setter
	def face(self, id):
		self._info("Changing face item to {}...".format(id))
		self._send_packet("s", "s#upf", id)
		packet = self.next("upf")
		if packet is None:
			raise ClientError("Failed to face head item to {}".format(id))
		self._info("Changed face item to {}".format(id))

	@property
	def neck(self):
		return self._penguins[self._id].neck

	@neck.setter
	def neck(self, id):
		self._info("Changing neck item to {}...".format(id))
		self._send_packet("s", "s#upn", id)
		packet = self.next("upn")
		if packet is None:
			raise ClientError("Failed to change neck item to {}".format(id))
		self._info("Changed neck item to {}".format(id))

	@property
	def body(self):
		return self._penguins[self._id].body

	@body.setter
	def body(self, id):
		self._info("Changing body item to {}...".format(id))
		self._send_packet("s", "s#upb", id)
		packet = self.next("upb")
		if packet is None:
			raise ClientError("Failed to change body item to {}".format(id))
		self._info("Changed body item to {}".format(id))

	@property
	def hand(self):
		return self._penguins[self._id].hand

	@hand.setter
	def hand(self, id):
		self._info("Changing hand item to {}...".format(id))
		self._send_packet("s", "s#upa", id)
		packet = self.next("upa")
		if packet is None:
			raise ClientError("Failed to change hand item to {}".format(id))
		self._info("Changed hand item to {}".format(id))

	@property
	def feet(self):
		return self._penguins[self._id].feet

	@feet.setter
	def feet(self, id):
		self._info("Changing feet item to {}...".format(id))
		self._send_packet("s", "s#upe", id)
		packet = self.next("upe")
		if packet is None:
			raise ClientError("Failed to change feet item to {}".format(id))
		self._info("Changed feet item to {}".format(id))

	@property
	def pin(self):
		return self._penguins[self._id].pin

	@pin.setter
	def pin(self, id):
		self._info("Changing pin to {}...".format(id))
		self._send_packet("s", "s#upl", id)
		packet = self.next("upl")
		if packet is None:
			raise ClientError("Failed to change pin to {}".format(id))
		self._info("Changed pin to {}".format(id))

	@property
	def background(self):
		return self._penguins[self._id].background

	@background.setter
	def background(self, id):
		self._info("Changing background to {}...".format(id))
		self._send_packet("s", "s#upp", id)
		packet = self.next("upp")
		if packet is None:
			raise ClientError("Failed to change background to {}".format(id))
		self._info("Changed background to {}".format(id))

	@property
	def x(self):
		return self._penguins[self._id].x

	@property
	def y(self):
		return self._penguins[self._id].y

	@property
	def inventory(self):
		self._info("Fetching inventory...")
		self._send_packet("s", "i#gi")
		packet = self.next("gi")
		if packet is None:
			raise ClientError("Failed to fetch inventory")
		return [int(id) for id in packet[4:-1]]

	@property
	def stamps(self):
		self._info("Fetching stamps...")
		self._send_packet("s", "st#gps")
		packet = self.next("gps")
		if packet is None:
			raise ClientError("Failed to fetch stamps")
		return packet[4:-1]

	def _heartbeat(self):
		if self._connected:
			self._heartbeat_timer = threading.Timer(600, self._heartbeat)
			self._heartbeat_timer.start()
			self._send_packet("s", "u#h")
		else:
			self._heartbeat_timer = None

	def walk(self, x, y, internal_room_id=False):
		self._info("Walking to ({}, {})...".format(x, y))
		if internal_room_id:
			self._send_packet("s", "u#sp", self._id, x, y)
		else:
			self._send_packet("s", "u#sp", None, self._id, x, y)
		packet = self.next("sp")
		if packet is None:
			raise ClientError("Failed to walk to ({}, {})".format(x, y))
		self._info("Walked to ({}, {})".format(x, y))

	def action(self, id):
		self._info("Performing action {}...".format(id))
		self._send_packet("s", "u#sa", id)
		packet = self.next("sa")
		if packet is None:
			raise ClientError("Failed to perform action {}".format(id))
		self._info("Performed action {}".format(id))

	@property
	def frame(self):
		return self._penguins[self._id].frame

	@frame.setter
	def frame(self, id):
		self._info("Setting frame to {}...".format(id))
		self._send_packet("s", "u#sf", id)
		packet = self.next("sf")
		if packet is None:
			raise ClientError("Failed to set frame to {}".format(id))
		self._info("Set frame to {}".format(id))

	def dance(self):
		self.frame = 26

	def wave(self):
		self.action(25)

	def sit(self, dir="s"):
		dirs = {
			"se": 24,
			"e": 23,
			"ne": 22,
			"n": 21,
			"nw": 20,
			"w": 19,
			"sw": 18,
			"s": 17
		}
		if dir not in dirs:
			dir = "s"
		self._info("Sitting in direction {}...".format(dir))
		self.frame = dirs[dir]
		self._info("Sat in direction {}".format(dir))

	def snowball(self, x, y):
		self._info("Throwing snowball to ({}, {})...".format(x, y))
		self._send_packet("s", "u#sb", x, y)
		packet = self.next("sb")
		if packet is None:
			raise ClientError("Failed to throw snowball to ({}, {})".format(x, y))
		self._info("Threw snowball to ({}, {})".format(x, y))

	def say(self, message, safe=False):
		if not message:
			raise ClientError("Cannot say nothing")
		self._info("Saying '{}'...".format(message))
		if safe:
			self._send_packet("s", "u#ss", message)
			packet = self.next("ss")
			if packet is None:
				raise ClientError("Failed to say '{}'".format(message))
		else:
			self._send_packet("s", "m#sm", self._id, message)
			packet = self.next("sm")
			if packet is None:
				raise ClientError("Failed to say '{}'".format(message))
		self._info("Said '{}'".format(message))

	def joke(self, id):
		self._info("Telling joke {}...".format(id))
		self._send_packet("s", "u#sj", None, self._id, id)
		packet = self.next("sj")
		if packet is None:
			raise ClientError("Failed to tell joke {}".format(id))
		self._info("Told joke {}".format(id))

	def emote(self, id):
		self._info("Reacting emote {}...".format(id))
		self._send_packet("s", "u#se", id)
		packet = self.next("se")
		if packet is None:
			raise ClientError("Failed to react emote {}".format(id))
		self._info("Reacted emote {}".format(id))

	def mail(self, id, postcard):
		self._info("Sending postcard #{}...".format(postcard))
		self._send_packet("s", "l#ms", id, postcard)
		packet = self.next("ms")
		if packet is None:
			raise ClientError("Failed to send postcard #{}".format(postcard))
		coins = int(packet[4])
		cost = self._coins - coins
		self._coins = coins
		sent = packet[5]
		if sent == "0":
			raise ClientError("Maximum postcards reached")
		if sent == "2":
			raise ClientError("Not enough coins")
		if sent == "1":
			self._info("Sent postcard #{}".format(postcard))
		raise ClientError("Invalid postcard response: {}".format(packet))

	def add_item(self, id):
		self._info("Adding item {}...".format(id))
		self._send_packet("s", "i#ai", id)
		packet = self.next("ai", lambda p: int(p[4]) == int(id))
		if packet is None:
			raise ClientError("Failed to add item {}".format(id))
		coins = int(packet[5])
		cost = self._coins - coins
		self._coins = coins
		self._info("Added item {}".format(id))

	# TODO
	def add_coins(self, coins):
		self._info("Adding {} coins...".format(coins))
		internal_room_id = self._internal_room_id
		self._internal_room_id = -1
		room = self._room
		self._send_packet("s", "j#jr", 912, 0, 0)
		packet = self.next("jg")
		if packet is None:
			raise ClientError("Failed to add {} coins".format(coins))
		self._send_packet("z", "zo", int(coins) * 10)
		packet = self.next("zo")
		if packet is None:
			raise ClientError("Failed to add {}".format(coins))
		coins = int(packet[4])
		earn = coins - self._coins
		self._coins = coins
		self._internal_room_id = internal_room_id
		self.room = room
		self._info("Added {} coins".format(earn))

	def add_stamp(self, id):
		self._info("Adding stamp {}...".format(id))
		self._send_packet("s", "st#sse", id)
		packet = self.next("sse")
		if packet is None:
			raise ClientError("Failed to add stamp {}".format(id))
		self._info("Added stamp {}".format(id))

	def add_igloo(self, id):
		self._info("Adding igloo {}...".format(id))
		self._send_packet("s", "g#au", None, self._id, id)
		packet = self.next("au")
		if packet is None:
			raise ClientError("Failed to add igloo {}".format(id))
		self._info("Added igloo {}".format(id))

	def add_furniture(self, id):
		self._info("Adding furniture {}...".format(id))
		self._send_packet("s", "g#af", id)
		packet = self.next("af")
		if packet is None:
			raise ClientError("Failed to add furniture {}".format(id))
		self._info("Added furniture {}".format(id))

	# TODO
	def igloo_music(self, id):
		self._info("Setting music to #{}...".format(id))
		self._send_packet("s", "g#go", None, self._id)
		# receive
		self._send_packet("s", "g#um", None, self._id, id)
		# receive
		self._info("Set music to #{}".format(id))

	def buddy(self, id):
		self._info("Sending buddy request to {}...".format(id))
		self._send_packet("s", "b#br", id)
		packet = self.next("br")
		if packet is None:
			raise ClientError("Failed to send buddy request to {}".format(id))
		self._info("Sent buddy request to {}".format(id))

	def follow(self, id, dx=0, dy=0):
		if id == self._id:
			raise ClientError("Cannot follow self")
		self._info("Following {}...".format(id))
		try:
			self.buddy(id)
		except ClientError:
			pass
		self._follow = (id, dx, dy)
		penguin = self._penguins[id]
		self.walk(penguin.x + dx, penguin.y + dy)
		self.color = penguin.color
		self.head = penguin.head
		self.face = penguin.face
		self.neck = penguin.neck
		self.body = penguin.body
		self.hand = penguin.hand
		self.feet = penguin.feet
		self.pin = penguin.pin
		self.background = penguin.background

	def unfollow(self):
		self._follow = None

	def logout(self):
		self._info("Logging out...")
		self._connected = False
		try:
			self.sock.shutdown(socket.SHUT_RDWR)
		except socket.error:
			pass
		self.sock.close()
