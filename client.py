import socket
import hashlib
import re
import os
import json
import threading
import Queue
from penguin import Penguin

class _Handler(object):
	def __init__(self, handlers, predicate):
		self._handlers = handlers
		self._predicate = predicate

	def handle(self, packet):
		return (self._predicate is None or self._predicate(packet)) and self.inner_handle(packet)

class _CallbackHandler(_Handler):
	def __init__(self, handlers, predicate, callback):
		super(_CallbackHandler, self).__init__(handlers, predicate)
		self._callback = callback

	def inner_handle(self, packet):
		if self._callback is not None:
			self._callback(packet)
		return True

	def __del__(self):
		self._handlers.remove(self)

class _OneTimeHandler(_Handler):
	def __init__(self, handlers, cmd, predicate, timeout):
		super(_OneTimeHandler, self).__init__(handlers, predicate)
		self._cmd = cmd
		self._timeout = timeout
		self._queue = Queue.Queue(1)

	def inner_handle(self, packet):
		if self._cmd is None or packet[2] == self._cmd:
			self._queue.put(packet)
			self._handlers.remove(self)
			return True
		return False

	@property
	def packet(self):
		try:
			return self._queue.get(timeout=self._timeout)
		except Queue.Empty:
			self._handlers.remove(self)
			return None

class ClientError(Exception):
	def __init__(self, msg, code=0):
		super(ClientError, self).__init__(msg)
		self.code = code			

class Client(object):
	def __init__(self, login_ip, login_port, game_ip, game_port, magic=None, logger=None):
		self._login_ip = login_ip
		self._login_port = login_port
		self._game_ip = game_ip
		self._game_port = game_port
		self._logger = logger
		self._magic = magic or "Y(02.>'H}t\":E1"
		self._connected = False
		self._buffer = ""
		self._handlers = {}
		self._nexts = []
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

	def _debug(self, msg):
		if self._logger is not None:
			self._logger.debug(msg)

	def _info(self, msg):
		if self._logger is not None:
			self._logger.info(msg)

	def _warning(self, msg):
		if self._logger is not None:
			self._logger.warning(msg)

	def _error(self, msg):
		if self._logger is not None:
			if isinstance(msg, list):
				filename = os.path.join(os.path.dirname(__file__), "json/errors.json")
				with open(filename) as file:
					data = json.load(file)
				code = int(msg[4])
				msg = "Error #" + str(code)
				if str(code) in data:
					msg += ": " + data[str(code)]
			self._logger.error(msg)

	def _critical(self, msg):
		if self._logger is not None:
			self._logger.critical(msg)

	def _send(self, data):
		self._debug("# SEND: " + str(data))
		try:
			self.sock.send(data + chr(0))
			return True
		except:
			self._critical("Connection lost")
			return False

	def _send_packet(self, ext, cmd, *args):
		packet = "%xt%" + ext + "%" + cmd + "%"
		if args and args[0] is None:
			args = args[1:]
		else:
			args = (self._internal_room_id,) + args
		packet += "%".join(str(arg) for arg in args) + "%"
		return self._send(packet)

	def _receive(self):
		data = ""
		try:
			while not chr(0) in self._buffer:
				data += self._buffer
				self._buffer = self.sock.recv(4096)
		except:
			return None
		i = self._buffer.index(chr(0)) + 1
		data += self._buffer[:i]
		self._buffer = self._buffer[i:]
		self._debug("# RECEIVE: " + str(data))
		return data

	def _receive_packet(self):
		data = self._receive()
		if data is None:
			return None
		if data.startswith("%"):
			packet = data.split('%')
			if packet[2] == "e":
				self._error(packet)
			return packet
		raise ClientError("Invalid packet")

	def _ver_check(self, ver):
		self._info("Sending 'verChk' request...")
		if not self._send('<msg t="sys"><body action="verChk" r="0"><ver v="' + str(ver) + '"/></body></msg>'):
		# if not self._send("<msg t='sys'><body action='verChk' r='0'><ver v='" + str(ver) + "' /></body></msg>"):
			return False
		data = self._receive()
		if data is None:
			return False
		if "apiOK" in data:
			self._info("Received 'apiOK' response")
			return True
		if "apiKO" in data:
			self._info("Received 'apiKO' response")
			return False
		raise ClientError("Invalid response")

	def _rndk(self):
		self._info("Sending rndK request...")
		if not self._send('<msg t="sys"><body action="rndK" r="-1"></body></msg>'):
		# if not self._send("<msg t='sys'><body action='rndK' r='-1'></body></msg>"):
			return None
		data = self._receive()
		if data is None:
			return None
		if "rndK" in data:
			key = re.search("<k>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/k>", data).group(1)
			self._info("Received key: " + key)
			return key
		raise ClientError("Invalid response")

	def _login(self, user, password, encrypted, ver):
		self._info("Logging in...")
		if not self._ver_check(ver):
			return None, False
		rndk = self._rndk()
		if rndk is None:
			return None, False
		hash = self._swapped_md5(self._swapped_md5(password, encrypted).upper() + rndk + self._magic)
		if not self._send('<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[' + user + ']]></nick><pword><![CDATA[' + hash + ']]></pword></login></body></msg>'):
		# if not self._send("<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[" + user + "]]></nick><pword><![CDATA[" + hash + "]]></pword></login></body></msg>"):
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
		if not self._send('<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[' + user + ']]></nick><pword><![CDATA[' + hash + ']]></pword></login></body></msg>'):
		# if not self._send("<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[" + user + "]]></nick><pword><![CDATA[" + hash + "]]></pword></login></body></msg>"):
			return None, False
		packet = self._receive_packet()
		if packet is None or packet[4] == "e":
			return packet, False
		while packet[2] != "l":
			packet = self._receive_packet()
			if packet is None or packet[4] == "e":
				return packet, False
		if not self._send_packet("s", "j#js", self._id, login_key, "en"):
			return None, False
		if confirmation is None:
			while packet[2] != "js":
				packet = self._receive_packet()
				if packet is None or packet[4] == "e":
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
		if packet[12]:
			member_left = int(packet[12])
		else:
			member_left = 0
		timezone = int(packet[13])
		# opened_playcard = packet[14] == '1'
		# saved_map_category = int(packet[15])
		# status_field = int(packet[16])

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
			room = int(packet[4])
			self.room = room

	def _jr(self, packet):
		self._internal_room_id = int(packet[3])
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
			color = int(packet[5])
			penguin.color = color
			if self._follow is not None and id == self._follow[0]:
				self.color = color

	def _uph(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			head = int(packet[5])
			penguin.head = head
			if self._follow is not None and id == self._follow[0]:
				self.head = head

	def _upf(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			face = int(packet[5])
			penguin.face = face
			if self._follow is not None and id == self._follow[0]:
				self.face = face

	def _upn(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			neck = int(packet[5])
			penguin.neck = neck
			if self._follow is not None and id == self._follow[0]:
				self.neck = neck

	def _upb(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			body = int(packet[5])
			penguin.body = body
			if self._follow is not None and id == self._follow[0]:
				self.body = body

	def _upa(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			hand = int(packet[5])
			penguin.hand = hand
			if self._follow is not None and id == self._follow[0]:
				self.hand = hand

	def _upe(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			feet = int(packet[5])
			penguin.feet = feet
			if self._follow is not None and id == self._follow[0]:
				self.feet = feet

	def _upl(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			pin = int(packet[5])
			penguin.pin = pin
			if self._follow is not None and id == self._follow[0]:
				self.pin = pin

	def _upp(self, packet):
		id = int(packet[4])
		if id in self._penguins:
			penguin = self._penguins[id]
			background = int(packet[5])
			penguin.background = background
			if self._follow is not None and id == self._follow[0]:
				self.background = background

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
		msg = packet[5]
		if self._follow is not None and id == self._follow[0]:
			self.say(msg)

	def _ss(self, packet):
		id = int(packet[4])
		msg = packet[5]
		if self._follow is not None and id == self._follow[0]:
			self.say(msg, True)

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
		thread = threading.Thread(target=self._heartbeat)
		thread.start()
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
		while self._connected:
			packet = self._receive_packet()
			if not self._connected or packet is None:
				break
			cmd = packet[2]
			handled = False
			if cmd in self._handlers:
				for handler in self._handlers[cmd]:
					if handler.handle(packet):
						handled = True
			for handler in self._nexts:
				if handler.handle(packet):
					handled = True
					break
			if not handled:
				self._warning("# UNHANDLED PACKET: " + '%'.join(packet))

	def connect(self, user, password, encrypted=False, ver=153):
		self._info("Connecting to login server at " + self._login_ip + ":" + str(self._login_port) + "...")
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect((self._login_ip, self._login_port))
		except:
			raise ClientError("Failed to connect to login server at " + self._login_ip + ":" + str(self._login_port))

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

		self._info("Connecting to game server at " + self._game_ip + ":" + str(self._game_port) + "...")
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.sock.connect((self._game_ip, self._game_port))
		except:
			raise ClientError("Failed to connect to game server at " + self._game_ip + ":" + str(self._game_port))

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

	def next(self, cmd=None, predicate=None, timeout=0.1):
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
		self._info("Joining room " + str(id) + "...")
		self._send_packet("s", "j#jr", id, x, y)
		packet = self.next("jr")
		if packet is None:
			raise ClientError("Failed to join room " + str(id))
		self._info("Joined room " + str(id))

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
		name = self._penguins[id].name if id in self._penguins else "Penguin " + str(id)
		self._info("Joining " + name + "'s igloo...")
		self._send_packet("s", "j#jp", None, self._id, int(id) + 1000)
		packet = self.next("jr")
		if packet is None:
			raise ClientError("Failed to join " + name + "'s igloo")
		self._info("Joined " + name + "'s igloo")

	@property
	def penguins(self):
		return self._penguins

	@property
	def color(self):
		return self._penguins[self._id].color

	@color.setter
	def color(self, id):
		self._info("Changing color to " + str(id) + "...")
		self._send_packet("s", "s#upc", id)
		packet = self.next("upc")
		if packet is None:
			raise ClientError("Failed to change color to " + str(id))
		self._info("Changed color to " + str(id) + "...")

	@property
	def head(self):
		return self._penguins[self._id].head

	@head.setter
	def head(self, id):
		self._info("Changing head item to " + str(id) + "...")
		self._send_packet("s", "s#uph", id)
		packet = self.next("uph")
		if packet is None:
			raise ClientError("Failed to change head item to " + str(id))
		self._info("Changed head item to " + str(id) + "...")

	@property
	def face(self):
		return self._penguins[self._id].face

	@face.setter
	def face(self, id):
		self._info("Changing face item to " + str(id) + "...")
		self._send_packet("s", "s#upf", id)
		packet = self.next("upf")
		if packet is None:
			raise ClientError("Failed to face head item to " + str(id))
		self._info("Changed face item to " + str(id) + "...")

	@property
	def neck(self):
		return self._penguins[self._id].neck

	@neck.setter
	def neck(self, id):
		self._info("Changing neck item to " + str(id) + "...")
		self._send_packet("s", "s#upn", id)
		packet = self.next("upn")
		if packet is None:
			raise ClientError("Failed to change neck item to " + str(id))
		self._info("Changed neck item to " + str(id) + "...")

	@property
	def body(self):
		return self._penguins[self._id].body

	@body.setter
	def body(self, id):
		self._info("Changing body item to " + str(id) + "...")
		self._send_packet("s", "s#upb", id)
		packet = self.next("upb")
		if packet is None:
			raise ClientError("Failed to change body item to " + str(id))
		self._info("Changed body item to " + str(id) + "...")

	@property
	def hand(self):
		return self._penguins[self._id].hand

	@hand.setter
	def hand(self, id):
		self._info("Changing hand item to " + str(id) + "...")
		self._send_packet("s", "s#upa", id)
		packet = self.next("upa")
		if packet is None:
			raise ClientError("Failed to change hand item to " + str(id))
		self._info("Changed hand item to " + str(id) + "...")

	@property
	def feet(self):
		return self._penguins[self._id].feet

	@feet.setter
	def feet(self, id):
		self._info("Changing feet item to " + str(id) + "...")
		self._send_packet("s", "s#upe", id)
		packet = self.next("upe")
		if packet is None:
			raise ClientError("Failed to change feet item to " + str(id))
		self._info("Changed feet item to " + str(id) + "...")

	@property
	def pin(self):
		return self._penguins[self._id].pin

	@pin.setter
	def pin(self, id):
		self._info("Changing pin to " + str(id) + "...")
		self._send_packet("s", "s#upl", id)
		packet = self.next("upl")
		if packet is None:
			raise ClientError("Failed to change pin to " + str(id))
		self._info("Changed pin to " + str(id) + "...")

	@property
	def background(self):
		return self._penguins[self._id].background

	@background.setter
	def background(self, id):
		self._info("Changing background to " + str(id) + "...")
		self._send_packet("s", "s#upp", id)
		packet = self.next("upp")
		if packet is None:
			raise ClientError("Failed to change background to " + str(id))
		self._info("Changed background to " + str(id) + "...")

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
		return packet[4:-1]

	@property
	def stamps(self):
		self._info("Fetching stamps...")
		self._send_packet("s", "st#gps")
		packet = self.next("gps")
		if packet is None:
			raise ClientError("Failed to fetch stamps")
		return packet[4:-1]

	def _heartbeat(self):
		threading.Timer(600, self._heartbeat)
		self._send_packet("s", "u#h")

	def walk(self, x, y):
		self._info("Walking to (" + str(x) + ", " + str(y) + ")...")
		self._send_packet("s", "u#sp", None, self._id, x, y)
		packet = self.next("sp")
		if packet is None:
			raise ClientError("Failed to walk to (" + str(x) + ", " + str(y) + ")")
		self._info("Walked to (" + str(x) + ", " + str(y) + ")")

	def action(self, id):
		self._info("Performing action " + str(id) + "...")
		self._send_packet("s", "u#sa", id)
		packet = self.next("sa")
		if packet is None:
			raise ClientError("Failed to perform action " + str(id))
		self._info("Performed action " + str(id))

	@property
	def frame(self):
		return self._penguins[self._id].frame

	@frame.setter
	def frame(self, id):
		self._info("Setting frame to " + str(id) + "...")
		self._send_packet("s", "u#sf", id)
		packet = self.next("sf")
		if packet is None:
			raise ClientError("Failed to set frame to " + str(id))
		self._info("Set frame to " + str(id))

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
		self._info("Sitting in direction " + dir + "...")
		self.frame = dirs[dir]
		self._info("Sat in direction " + dir)

	def snowball(self, x, y):
		self._info("Throwing snowball to (" + str(x) + ", " + str(y) + ")...")
		self._send_packet("s", "u#sb", x, y)
		packet = self.next("sb")
		if packet is None:
			raise ClientError("Failed to throw snowball to (" + str(x) + ", " + str(y) + ")...")
		self._info("Threw snowball to (" + str(x) + ", " + str(y) + ")")

	def say(self, msg, safe=False):
		self._info("Saying '" + str(msg) + "'...")
		if safe:
			self._send_packet("s", "u#ss", msg)
			packet = self.next("ss")
			if packet is None:
				raise ClientError("Failed to say '" + str(msg) + "'")
		else:
			self._send_packet("s", "m#sm", self._id, msg)
			packet = self.next("sm")
			if packet is None:
				raise ClientError("Failed to say '" + str(msg) + "'")
		self._info("Said '" + str(msg) + "'")

	def joke(self, id):
		self._info("Telling joke " + str(id) + "...")
		self._send_packet("s", "u#sj", None, self._id, id)
		packet = self.next("sj")
		if packet is None:
			raise ClientError("Failed to tell joke " + str(id))
		self._info("Told joke " + str(id))

	def emote(self, id):
		self._info("Reacting emote " + str(id) + "...")
		self._send_packet("s", "u#se", id)
		packet = self.next("se")
		if packet is None:
			raise ClientError("Failed to react emote " + str(id))
		self._info("Reacted emote " + str(id))

	def mail(self, id, postcard):
		self._info("Sending postcard #" + str(postcard) + "...")
		self._send_packet("s", "l#ms", id, postcard)
		packet = self.next("ms")
		if packet is None:
			raise ClientError("Failed to send postcard #" + str(postcard))
		coins = int(packet[4])
		cost = self._coins - coins
		self._coins = coins
		sent = packet[5]
		if sent == "0":
			raise ClientError("Maximum postcards reached")
		if sent == "1":
			self._info("Sent postcard #" + str(postcard))
		if sent == "2":
			raise ClientError("Not enough coins")
		raise ClientError("Invalid response")

	def add_item(self, id):
		self._info("Adding item " + str(id) + "...")
		self._send_packet("s", "i#ai", id)
		packet = self.next("ai", lambda p: int(p[4]) == int(id))
		if packet is None:
			raise ClientError("Failed to add item " + str(id))
		coins = int(packet[5])
		cost = self._coins - coins
		self._coins = coins
		self._info("Added item " + str(id))

	# TODO
	def add_coins(self, coins):
		self._info("Adding " + str(coins) + " coins...")
		room = self._room
		self._send_packet("s", "j#jr", 912, 0, 0)
		packet = self.next("jg")
		if packet is None:
			raise ClientError("Failed to add " + str(coins) + "coins")
		self.frame = 23
		self.frame = 21
		self.frame = 17
		self.frame = 23
		self.frame = 17
		self.frame = 19
		self.frame = 21
		self._send_packet("z", "zo", int(coins) * 10)
		packet = self.next("zo")
		if packet is None:
			raise ClientError("Failed to add " + str(coins) + "coins")
		coins = int(packet[4])
		earn = coins - self._coins
		self._coins = coins
		self.room = room
		self._info("Added " + str(earn) + " coins")

	def add_stamp(self, id):
		self._info("Adding stamp " + str(id) + "...")
		self._send_packet("s", "st#sse", id)
		packet = self.next("sse")
		if packet is None:
			raise ClientError("Failed to add stamp " + str(id))
		self._info("Added stamp " + str(id))

	def add_igloo(self, id):
		self._info("Adding igloo " + str(id) + "...")
		self._send_packet("s", "g#au", None, self._id, id)
		packet = self.next("au")
		if packet is None:
			raise ClientError("Failed to add igloo " + str(id))
		self._info("Added igloo " + str(id))

	def add_furniture(self, id):
		self._info("Adding furniture " + str(id) + "...")
		self._send_packet("s", "g#af", id)
		packet = self.next("af")
		if packet is None:
			raise ClientError("Failed to add furniture " + str(id))
		self._info("Added furniture " + str(id))

	# TODO
	def igloo_music(self, id):
		self._info("Setting music to #" + str(id) + "...")
		self._send_packet("s", "g#go", None, self._id)
		# receive
		self._send_packet("s", "g#um", None, self._id, id)
		# receive
		self._info("Set music to #" + str(id))

	def buddy(self, id):
		self._info("Sending buddy request to " + str(id) + "...")
		self._send_packet("s", "b#br", id)
		packet = self.next("br")
		if packet is None:
			raise ClientError("Failed to send buddy request to " + str(id))
		self._info("Sent buddy request to " + str(id))

	def follow(self, id, dx=0, dy=0):
		if id == self._id:
			raise ValueError("Cannot follow self")
		self._info("Following " + str(id) + "...")
		self.buddy(id)
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
		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()
