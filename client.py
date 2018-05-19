import sys
import socket
import hashlib
import re
from threading import Thread, Timer
from multiprocessing.pool import ThreadPool
import Queue
import logging
from bisect import insort
import common
from penguin import Penguin
from aes import AES

class _ExceptionThread(Thread):
	def __init__(self, *args, **kwargs):
		super(_ExceptionThread, self).__init__(*args, **kwargs)
		self._exc_type = None
		self._exc = None
		self._exc_tb = None

	def run(self, *args, **kwargs):
		try:
			super(_ExceptionThread, self).run(*args, **kwargs)
		except:
			self._exc_type, self._exc, self._exc_tb = sys.exc_info()

	def join(self, *args, **kwargs):
		super(_ExceptionThread, self).join(*args, **kwargs)
		if self._exc is not None:
			raise self._exc_type, self._exc, self._exc_tb

class _Handler(object):
	def __init__(self, handlers, predicate):
		self._handlers = handlers
		self._predicate = predicate

	def handle(self, packet):
		if self._predicate is None or self._predicate(packet):
			thread = _ExceptionThread(target=self.inner_handle, args=(packet,))
			thread.start()
			return thread
		return None

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
		self._packet = Queue.Queue(1)

	def inner_handle(self, packet):
		self._packet.put(packet)

	@property
	def packet(self):
		try:
			return self._packet.get(timeout=self._timeout)
		except Queue.Empty:
			return None
		finally:
			self._handlers.remove(self)

	def cancel(self):
		self._packet.put(None)

class ClientError(Exception):
	def __init__(self, client, message, code=0):
		super(ClientError, self).__init__(message)
		self.client = client
		self.code = code

class Client(object):
	def __init__(self, login_ip, login_port, game_ip, game_port, magic=None, single_quotes=False, logger=None):
		self._login_ip = login_ip
		self._login_port = login_port
		self._game_ip = game_ip
		self._game_port = game_port
		self._magic = "Y(02.>'H}t\":E1" if magic is None else magic
		self._single_quotes = single_quotes
		if logger is None:
			logger = logging.getLogger()
			logger.setLevel(logging.NOTSET)
			handler = logging.StreamHandler(sys.stdout)
			logger.addHandler(handler)
		self._logger = logger

		self._connected = False
		self._buffer = ""
		self._handlers = {}
		self._nexts = []
		self._heartbeat_timer = None
		self._internal_room_id = -1
		self._id = -1
		self._coins = -1
		self._room = -1
		self._all_penguins = {}
		self._penguins = {}
		self._inventory = None
		self._buddies = None
		self._follow = None

	def __iter__(self):
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc, exc_tb):
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
		if isinstance(message, list):
			code = int(message[4])
			message = common.get_json("errors").get(str(code), "")
			if self._logger is not None:
				if message:
					self._logger.error("Error #{}: {}".format(code, message))
				else:
					self._logger.error("Error #{}".format(code))
			raise ClientError(self, message, code)
		if self._logger is not None:
			self._logger.error(message)
		raise ClientError(self, message)

	def _critical(self, message):
		if self._logger is not None:
			self._logger.critical(message)
		raise ClientError(self, message)

	def _require_int(self, name, value):
		try:
			return int(value)
		except ValueError:
			self._error("{} must be int".format(name))

	def _send(self, data):
		self._debug("# Send: {}".format(data))
		try:
			self._sock.send(data + chr(0))
		except socket.error:
			self._critical("Connection lost")

	def _send_packet(self, ext, cmd, *args):
		packet = "%xt%{}%{}%".format(ext, cmd)
		if args and args[0] is None:
			args = args[1:]
		else:
			packet += str(self._internal_room_id) + "%"
		packet += "".join(str(arg) + "%" for arg in args)
		self._send(packet)

	def _receive(self):
		data = ""
		while not chr(0) in self._buffer:
			data += self._buffer
			try:
				self._buffer = self._sock.recv(4096)
			except socket.error:
				self._critical("Connection lost")
		i = self._buffer.index(chr(0))
		data += self._buffer[:i]
		self._buffer = self._buffer[i + 1:]
		self._debug("# Receive: {}".format(data))
		return data

	def _receive_packet(self, error=False):
		data = self._receive()
		while not data.startswith("%"):
			data = self._receive()
		packet = data.split("%")
		if not error and packet[2] == "e":
			self._error(packet)
		return packet

	def _ver_check(self, ver):
		self._info("Sending 'verChk' request...")
		if self._single_quotes:
			data = "<msg t='sys'><body action='verChk' r='0'><ver v='{}' /></body></msg>".format(ver)
		else:
			data = '<msg t="sys"><body action="verChk" r="0"><ver v="{}"/></body></msg>'.format(ver)
		self._send(data)
		data = self._receive()
		if "cross-domain-policy" in data:
			data = self._receive()
		if "apiKO" in data:
			self._error('Received "apiKO" response')
		if "apiOK" in data:
			self._info('Received "apiOK" response')
		else:
			self._error("Invalid verChk response: {}".format(data))

	def _rndk(self):
		self._info("Sending rndK request...")
		if self._single_quotes:
			data = "<msg t='sys'><body action='rndK' r='-1'></body></msg>"
		else:
			data = '<msg t="sys"><body action="rndK" r="-1"></body></msg>'
		self._send(data)
		data = self._receive()
		if "rndK" not in data:
			self._error("Invalid rndk response: {}".format(data))
		key = re.search(r"<k>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?<\/k>", data).group(1)
		self._info("Received key: {}".format(key))
		return key

	def _recaptcha(self):
		try:
			import recaptcha
		except ImportError:
			self._error("Failed to retrieve reCAPTCHA token: cefpython is not installed; Please install it using the following command and try again:\npip install cefpython3")
		self._info("Retrieving reCAPTCHA token...")
		token = recaptcha.get_token()
		if token is None:
			self._error("Failed to retrieve reCAPTCHA token")
		self._info("reCAPTCHA token: {}".format(token))
		self._send_packet("s", "rewritten#captchaverify", token)
		packet = self._receive_packet()
		while packet[2] != "captchasuccess":
			packet = self._receive_packet()

	def _login(self, user, password, encrypted, ver):
		self._info("Connecting to login server at {}:{}...".format(self._login_ip, self._login_port))
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self._sock.connect((self._login_ip, self._login_port))
		except socket.error:
			self._error("Failed to connect to login server at {}:{}".format(self._login_ip, self._login_port))

		try:
			self._info("Logging in...")
			self._ver_check(ver)
			rndk = self._rndk()
			if self._magic:
				digest = self._swapped_md5(self._swapped_md5(password, encrypted).upper() + rndk + self._magic)
				if self._login_ip == "198.100.148.54":
					aes = AES(256, 256)
					digest = aes.encrypt(digest, "67L8CALPPCD4J283WL3JF3T2T32DFGZ8", "ECB")
			else:
				digest = password
			if self._single_quotes:
				data = "<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>".format(user, digest)
			else:
				data = '<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>'.format(user, digest)
			self._send(data)
			packet = self._receive_packet()
			while packet[2] != "l":
				packet = self._receive_packet()
			self._info("Logged in")
			return packet
		finally:
			try:
				self._sock.shutdown(socket.SHUT_RDWR)
			except socket.error:
				pass
			self._sock.close()

	def _join_server(self, user, login_key, confirmation, ver):
		self._info("Connecting to game server at {}:{}...".format(self._game_ip, self._game_port))
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self._sock.connect((self._game_ip, self._game_port))
		except socket.error:
			self._error("Failed to connect to game server at {}:{}".format(self._game_ip, self._game_port))

		self._info("Joining server...")
		self._ver_check(ver)
		rndk = self._rndk()
		digest = self._swapped_md5(login_key + rndk) + login_key
		if confirmation is not None:
			digest += "#" + confirmation
		if self._single_quotes:
			data = "<msg t='sys'><body action='login' r='0'><login z='w1'><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>".format(user, digest)
		else:
			data = '<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[{}]]></nick><pword><![CDATA[{}]]></pword></login></body></msg>'.format(user, digest)
		self._send(data)
		packet = self._receive_packet()
		while packet[2] != "l":
			packet = self._receive_packet()
		self._send_packet("s", "j#js", self._id, login_key, "en")
		if confirmation is None:
			while packet[2] != "js":
				packet = self._receive_packet()
				if packet[2] == "joincaptcha":
					self._recaptcha()
		self._info("Joined server")

	def _heartbeat(self):
		self._heartbeat_timer = Timer(600, self._heartbeat)
		self._heartbeat_timer.start()
		try:
			self._send_packet("s", "u#h")
		except ClientError:
			pass

	def _e(self, packet):
		self._error(packet)

	def _lp(self, packet):
		del self._handlers["lp"]
		penguin = Penguin.from_player(packet[4])
		self._all_penguins[penguin.id] = penguin
		self._penguins[penguin.id] = penguin
		self._coins = int(packet[5])
		safemode = packet[6] == "1"
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
		# opened_playcard = packet[14] == "1"
		# saved_map_category = int(packet[15])
		# status_field = int(packet[16])
		self._heartbeat()

	def _ap(self, packet):
		penguin = Penguin.from_player(packet[4])
		self._all_penguins[penguin.id] = penguin
		self._penguins[penguin.id] = penguin

	def _rp(self, packet):
		penguin_id = int(packet[4])
		if penguin_id in self._penguins:
			penguin = self._penguins.pop(penguin_id)
		if self._follow is not None and penguin_id == self._follow[0]:
			try:
				room_id = self.find_buddy(penguin_id)
			except ClientError:
				self.unfollow()
			self.room = room_id

	def _jr(self, packet):
		internal_room_id = int(packet[3])
		self._internal_room_id = internal_room_id
		self._room = int(packet[4])
		self._penguins.clear()
		for player in packet[5:-1]:
			penguin = Penguin.from_player(player)
			self._penguins[penguin.id] = penguin
		self._all_penguins.update(self._penguins)

	def _br(self, packet):
		penguin_id = int(packet[4])
		penguin_name = packet[5]
		self._info('Received a buddy request from "{}"'.format(penguin_name))
		self._info('Accepting buddy "{}"...'.format(penguin_name))
		self._send_packet("s", "b#ba", penguin_id)
		packet = self.next("ba")
		if packet is None:
			self._error('Failed to accept buddy "{}"'.format(penguin_name))
		if self._buddies is not None:
			penguin_id = int(packet[4])
			penguin_name = packet[5]
			penguin = Penguin(penguin_id, penguin_name, None, None, None, None, None, None, None, None, None, None)
			penguin.online = True
			self._buddies[penguin.id] = penguin
		self._info('Accepted buddy "{}"'.format(penguin_name))

	def _rb(self, packet):
		penguin_id = int(packet[4])
		if self._buddies is not None and penguin_id in self._buddies:
			del self._buddies[penguin_id]

	def _bon(self, packet):
		penguin_id = int(packet[4])
		if self._buddies is not None and penguin_id in self._buddies:
			self._buddies[penguin_id].online = True

	def _bof(self, packet):
		penguin_id = int(packet[4])
		if self._buddies is not None and penguin_id in self._buddies:
			self._buddies[penguin_id].online = False

	def _upc(self, packet):
		penguin_id = int(packet[4])
		color = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].color = color
		if penguin_id in self._penguins:
			self._penguins[penguin_id].color = color
			if self._follow is not None and penguin_id == self._follow[0]:
				self.color = color

	def _uph(self, packet):
		penguin_id = int(packet[4])
		head = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].head = head
		if penguin_id in self._penguins:
			self._penguins[penguin_id].head = head
			if self._follow is not None and penguin_id == self._follow[0]:
				self.head = head

	def _upf(self, packet):
		penguin_id = int(packet[4])
		face = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].face = face
		if penguin_id in self._penguins:
			self._penguins[penguin_id].face = face
			if self._follow is not None and penguin_id == self._follow[0]:
				self.face = face

	def _upn(self, packet):
		penguin_id = int(packet[4])
		neck = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].neck = neck
		if penguin_id in self._penguins:
			self._penguins[penguin_id].neck = neck
			if self._follow is not None and penguin_id == self._follow[0]:
				self.neck = neck

	def _upb(self, packet):
		penguin_id = int(packet[4])
		body = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].body = body
		if penguin_id in self._penguins:
			self._penguins[penguin_id].body = body
			if self._follow is not None and penguin_id == self._follow[0]:
				self.body = body

	def _upa(self, packet):
		penguin_id = int(packet[4])
		hand = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].hand = hand
		if penguin_id in self._penguins:
			self._penguins[penguin_id].hand = hand
			if self._follow is not None and penguin_id == self._follow[0]:
				self.hand = hand

	def _upe(self, packet):
		penguin_id = int(packet[4])
		feet = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].feet = feet
		if penguin_id in self._penguins:
			self._penguins[penguin_id].feet = feet
			if self._follow is not None and penguin_id == self._follow[0]:
				self.feet = feet

	def _upl(self, packet):
		penguin_id = int(packet[4])
		pin = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].pin = pin
		if penguin_id in self._penguins:
			self._penguins[penguin_id].pin = pin
			if self._follow is not None and penguin_id == self._follow[0]:
				self.pin = pin

	def _upp(self, packet):
		penguin_id = int(packet[4])
		background = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].background = background
		if penguin_id in self._penguins:
			self._penguins[penguin_id].background = background
			if self._follow is not None and penguin_id == self._follow[0]:
				self.background = background

	def _sp(self, packet):
		penguin_id = int(packet[4])
		x = int(packet[5])
		y = int(packet[6])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].x = x
			self._all_penguins[penguin_id].y = y
		if penguin_id in self._penguins:
			self._penguins[penguin_id].x = x
			self._penguins[penguin_id].y = y
			if self._follow is not None and penguin_id == self._follow[0]:
				self.walk(x + self._follow[1], y + self._follow[2])

	def _sa(self, packet):
		penguin_id = int(packet[4])
		if penguin_id in self._penguins:
			action_id = int(packet[5])
			if self._follow is not None and penguin_id == self._follow[0]:
				self.action(action_id)

	def _sf(self, packet):
		penguin_id = int(packet[4])
		frame = int(packet[5])
		if penguin_id in self._all_penguins:
			self._all_penguins[penguin_id].frame = frame
		if penguin_id in self._penguins:
			self._penguins[penguin_id].frame = frame
			if self._follow is not None and penguin_id == self._follow[0]:
				self.frame = frame

	def _sb(self, packet):
		penguin_id = int(packet[4])
		x = int(packet[5])
		y = int(packet[6])
		if self._follow is not None and penguin_id == self._follow[0]:
			self.snowball(x, y)

	def _sm(self, packet):
		penguin_id = int(packet[4])
		message = packet[5]
		if self._follow is not None and penguin_id == self._follow[0]:
			self.say(message)

	def _ss(self, packet):
		penguin_id = int(packet[4])
		message = packet[5]
		if self._follow is not None and penguin_id == self._follow[0]:
			self.say(message, True)

	def _sj(self, packet):
		penguin_id = int(packet[4])
		joke_id = int(packet[5])
		if self._follow is not None and penguin_id == self._follow[0]:
			self.joke(joke_id)

	def _se(self, packet):
		penguin_id = int(packet[4])
		emote_id = int(packet[5])
		if self._follow is not None and penguin_id == self._follow[0]:
			self.emote(emote_id)

	def _ms(self, packet):
		self._coins = int(packet[4])

	def _ai(self, packet):
		item_id = int(packet[4])
		self._coins = int(packet[5])
		if self._inventory is not None:
			insort(self._inventory, item_id)

	def _zo(self, packet):
		self._coins = int(packet[4])

	def _game(self):
		self.handle("h")
		self.handle("e", self._e)
		self.handle("lp", self._lp)
		self.handle("ap", self._ap)
		self.handle("rp", self._rp)
		self.handle("jr", self._jr)
		self.handle("br", self._br)
		self.handle("rb", self._rb)
		self.handle("bon", self._bon)
		self.handle("bof", self._bof)
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
		self.handle("ms", self._ms)
		self.handle("ai", self._ai)
		self.handle("zo", self._zo)

		threads = set()
		while self._connected:
			try:
				packet = self._receive_packet(True)
			except ClientError:
				self.logout()
			if not self._connected:
				break
			cmd = packet[2]
			handled = False

			if cmd in self._handlers:
				for handler in self._handlers[cmd]:
					thread = handler.handle(packet)
					if thread is not None:
						threads.add(thread)
						handled = True

			for handler in self._nexts:
				thread = handler.handle(packet)
				if thread is not None:
					threads.add(thread)
					handled = True
					break

			if not handled:
				self._warning("# Unhandled packet: {}".format("%".join(packet)))

			alive = set()
			for thread in threads:
				if thread.is_alive():
					alive.add(thread)
				else:
					try:
						thread.join()
					except ClientError:
						pass
			threads = alive

	def connect(self, user, password, encrypted=False, ver=153):
		packet = self._login(user, password, encrypted, ver)
		if "|" in packet[4]:
			user = packet[4]
			data = packet[4].split("|")
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

		self._join_server(user, login_key, confirmation, ver)
		self._connected = True
		thread = Thread(target=self._game)
		thread.start()

	def handle(self, cmd, callback=None, predicate=None):
		if cmd not in self._handlers:
			self._handlers[cmd] = set()
		handler = _CallbackHandler(self._handlers[cmd], predicate, callback)
		self._handlers[cmd].add(handler)
		return handler

	def next(self, cmd=None, predicate=None, timeout=5):
		handler = _OneTimeHandler(self._nexts, cmd, predicate, timeout)
		self._nexts.append(handler)
		return handler.packet

	def get_penguin_id(self, penguin_id_or_name):
		try:
			return int(penguin_id_or_name)
		except ValueError:
			pass
		penguins = self._all_penguins.values()
		if self._buddies is not None:
			penguins.extend(self._buddies.values())
		for penguin in penguins:
			if penguin.name.lower() == penguin_id_or_name.lower():
				return penguin.id
		self._error('Penguin "{}" not found'.format(penguin_id_or_name))

	def get_penguin(self, penguin_id):
		penguin_id = self._require_int("penguin_id", penguin_id)
		if penguin_id in self._all_penguins:
			return self._all_penguins[penguin_id]
		self._info("Fetching player information...")
		self._send_packet("s", "u#gp", penguin_id)
		packet = self.next("gp")
		if packet is None:
			self._error("Failed to fetch player information")
		try:
			penguin = Penguin.from_player(packet[4])
		except ValueError as e:
			self._error(e.message)
		self._all_penguins[penguin.id] = penguin
		return penguin

	def get_room_id(self, room_id_or_name):
		try:
			return int(room_id_or_name)
		except ValueError:
			pass
		for room_id, room_name in common.get_json("rooms").iteritems():
			if room_name == room_id_or_name.lower():
				return int(room_id)
		self._error('Room "{}" not found'.format(room_id_or_name))

	def get_room_name(self, room_id):
		room_id = self._require_int("room_id", room_id)
		if room_id > 1000:
			return "{}'s igloo".format(self.get_penguin(room_id - 1000).name)
		return common.get_json("rooms").get(str(room_id), "room {}".format(room_id))

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
	def room(self, room_id, x=0, y=0):
		x = self._require_int("x", x)
		y = self._require_int("y", y)
		room_name = self.get_room_name(room_id)
		self._info("Joining {}...".format(room_name))
		self._send_packet("s", "j#jr", room_id, x, y)
		if self.next("jr") is None:
			self._error("Failed to join {}".format(room_name))
		self._info("Joined {}".format(room_name))

	@property
	def igloo(self):
		return self._room - 1000 if self._room > 1000 else None

	@igloo.setter
	def igloo(self, penguin_id):
		penguin = self.get_penguin(penguin_id)
		self._info("Joining {}'s igloo...".format(penguin.name))
		self._send_packet("s", "j#jp", int(penguin_id) + 1000)
		if self.next("jr") is None:
			self._error("Failed to join {}'s igloo".format(penguin.name))
		self._info("Joined {}'s igloo".format(penguin.name))

	@property
	def penguins(self):
		return self._penguins.copy()

	@property
	def color(self):
		return self._penguins[self._id].color

	@color.setter
	def color(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing color to {}...".format(item_id))
		self._send_packet("s", "s#upc", item_id)
		if self.next("upc") is None:
			self._error("Failed to change color to {}".format(item_id))
		self._info("Changed color to {}".format(item_id))

	@property
	def head(self):
		return self._penguins[self._id].head

	@head.setter
	def head(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing head item to {}...".format(item_id))
		self._send_packet("s", "s#uph", item_id)
		if self.next("uph") is None:
			self._error("Failed to change head item to {}".format(item_id))
		self._info("Changed head item to {}".format(item_id))

	@property
	def face(self):
		return self._penguins[self._id].face

	@face.setter
	def face(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing face item to {}...".format(item_id))
		self._send_packet("s", "s#upf", item_id)
		if self.next("upf") is None:
			self._error("Failed to change face item to {}".format(item_id))
		self._info("Changed face item to {}".format(item_id))

	@property
	def neck(self):
		return self._penguins[self._id].neck

	@neck.setter
	def neck(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing neck item to {}...".format(item_id))
		self._send_packet("s", "s#upn", item_id)
		if self.next("upn") is None:
			self._error("Failed to change neck item to {}".format(item_id))
		self._info("Changed neck item to {}".format(item_id))

	@property
	def body(self):
		return self._penguins[self._id].body

	@body.setter
	def body(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing body item to {}...".format(item_id))
		self._send_packet("s", "s#upb", item_id)
		if self.next("upb") is None:
			self._error("Failed to change body item to {}".format(item_id))
		self._info("Changed body item to {}".format(item_id))

	@property
	def hand(self):
		return self._penguins[self._id].hand

	@hand.setter
	def hand(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing hand item to {}...".format(item_id))
		self._send_packet("s", "s#upa", item_id)
		if self.next("upa") is None:
			self._error("Failed to change hand item to {}".format(item_id))
		self._info("Changed hand item to {}".format(item_id))

	@property
	def feet(self):
		return self._penguins[self._id].feet

	@feet.setter
	def feet(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing feet item to {}...".format(item_id))
		self._send_packet("s", "s#upe", item_id)
		if self.next("upe") is None:
			self._error("Failed to change feet item to {}".format(item_id))
		self._info("Changed feet item to {}".format(item_id))

	@property
	def pin(self):
		return self._penguins[self._id].pin

	@pin.setter
	def pin(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing pin to {}...".format(item_id))
		self._send_packet("s", "s#upl", item_id)
		if self.next("upl") is None:
			self._error("Failed to change pin to {}".format(item_id))
		self._info("Changed pin to {}".format(item_id))

	@property
	def background(self):
		return self._penguins[self._id].background

	@background.setter
	def background(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Changing background to {}...".format(item_id))
		self._send_packet("s", "s#upp", item_id)
		if self.next("upp") is None:
			self._error("Failed to change background to {}".format(item_id))
		self._info("Changed background to {}".format(item_id))

	@property
	def x(self):
		return self._penguins[self._id].x

	@property
	def y(self):
		return self._penguins[self._id].y

	@property
	def inventory(self):
		if self._inventory is None:
			self._info("Fetching inventory...")
			self._send_packet("s", "i#gi")
			packet = self.next("gi")
			if packet is None:
				self._error("Failed to fetch inventory")
			self._info("Fetched inventory")
			self._inventory = [int(item_id) for item_id in packet[4:-1] if item_id]
			self._inventory.sort()
		return self._inventory

	@property
	def buddies(self):
		if self._buddies is None:
			self._info("Fetching buddies...")
			self._send_packet("s", "b#gb")
			packet = self.next("gb")
			if packet is None:
				self._error("Faild to fetch buddies")
			self._info("Fetched buddies")
			self._buddies = {}
			for buddy in packet[4:-1]:
				if buddy:
					penguin = Penguin.from_buddy(buddy)
					self._buddies[penguin.id] = penguin
		return self._buddies

	@property
	def stamps(self):
		return self.get_stamps(self._id)

	def get_stamps(self, penguin_id):
		penguin = self.get_penguin(penguin_id)
		self._info('Fetching stamps of "{}"...'.format(penguin.name))
		self._send_packet("s", "st#gps", penguin_id)
		packet = self.next("gps")
		if packet is None:
			self._error('Failed to fetch stamps of "{}"'.format(penguin.name))
		self._info('Fetched stamps of "{}"'.format(penguin.name))
		return [int(stamp_id) for stamp_id in packet[5].split("|") if stamp_id]

	def walk(self, x, y):
		x = self._require_int("x", x)
		y = self._require_int("y", y)
		self._info("Walking to ({}, {})...".format(x, y))
		if self._login_ip == "server.cprewritten.net":
			self._send_packet("s", "u#sp", x, y)
		else:
			self._send_packet("s", "u#sp", None, self._id, x, y)
		if self.next("sp") is None:
			self._error("Failed to walk to ({}, {})".format(x, y))
		self._info("Walked to ({}, {})".format(x, y))

	def action(self, action_id):
		action_id = self._require_int("action_id", action_id)
		self._info("Performing action {}...".format(action_id))
		self._send_packet("s", "u#sa", action_id)
		if self.next("sa") is None:
			self._error("Failed to perform action {}".format(action_id))
		self._info("Performed action {}".format(action_id))

	@property
	def frame(self):
		return self._penguins[self._id].frame

	@frame.setter
	def frame(self, frame_id):
		frame_id = self._require_int("frame_id", frame_id)
		self._info("Setting frame to {}...".format(frame_id))
		self._send_packet("s", "u#sf", frame_id)
		if self.next("sf") is None:
			self._error("Failed to set frame to {}".format(frame_id))
		self._info("Set frame to {}".format(frame_id))

	def dance(self):
		self.frame = 26

	def wave(self):
		self.action(25)

	def sit(self, direction="s"):
		directions = {
			"se": 24,
			"e": 23,
			"ne": 22,
			"n": 21,
			"nw": 20,
			"w": 19,
			"sw": 18,
			"s": 17
		}
		if direction not in directions:
			self._error('Unknown sit direction "{}"'.format(direction))
		self._info("Sitting in direction {}...".format(direction))
		self.frame = directions[direction]
		self._info("Sat in direction {}".format(direction))

	def snowball(self, x, y):
		x = self._require_int("x", x)
		y = self._require_int("y", y)
		self._info("Throwing snowball to ({}, {})...".format(x, y))
		self._send_packet("s", "u#sb", x, y)
		if self.next("sb") is None:
			self._error("Failed to throw snowball to ({}, {})".format(x, y))
		self._info("Threw snowball to ({}, {})".format(x, y))

	def say(self, message, safe=False):
		if safe:
			message = self._require_int("message", message)
			self._info('Saying {}...'.format(message))
			self._send_packet("s", "u#ss", message)
			if self.next("ss") is None:
				self._error('Failed to say "{}"'.format(message))
			self._info('Said {}'.format(message))
		else:
			if not message:
				self._error("Cannot say nothing")
			self._info('Saying "{}"...'.format(message))
			self._send_packet("s", "m#sm", self._id, message)
			if self.next("sm") is None:
				self._error('Failed to say "{}"'.format(message))
			self._info('Said "{}"'.format(message))

	def joke(self, joke_id):
		joke_id = self._require_int("joke_id", joke_id)
		self._info("Telling joke {}...".format(joke_id))
		self._send_packet("s", "u#sj", None, self._id, joke_id)
		if self.next("sj") is None:
			self._error("Failed to tell joke {}".format(joke_id))
		self._info("Told joke {}".format(joke_id))

	def emote(self, emote_id):
		emote_id = self._require_int("emote_id", emote_id)
		self._info("Reacting emote {}...".format(emote_id))
		self._send_packet("s", "u#se", emote_id)
		if self.next("se") is None:
			self._error("Failed to react emote {}".format(emote_id))
		self._info("Reacted emote {}".format(emote_id))

	def mail(self, penguin_id, postcard_id):
		postcard_id = self._require_int("postcard_id", postcard_id)
		penguin = self.get_penguin(penguin_id)
		self._info('Sending postcard #{} to "{}"...'.format(postcard_id, penguin.name))
		self._send_packet("s", "l#ms", penguin.id, postcard_id)
		coins = self._coins
		packet = self.next("ms")
		if packet is None:
			self._error('Failed to send postcard #{} to "{}"'.format(postcard_id, penguin.name))
		cost = coins - int(packet[4])
		status = packet[5]
		if status == "0":
			self._error("Maximum postcards reached")
		if status == "1":
			self._info('Sent postcard #{} to "{}"'.format(postcard_id, penguin.name))
			return
		if status == "2":
			self._error("Not enough coins")
		self._error("Invalid postcard response: {}".format(packet))

	def add_item(self, item_id):
		item_id = self._require_int("item_id", item_id)
		self._info("Adding item {}...".format(item_id))
		self._send_packet("s", "i#ai", item_id)
		coins = self._coins
		packet = self.next("ai", lambda p: int(p[4]) == item_id)
		if packet is None:
			self._error("Failed to add item {}".format(item_id))
		cost = coins - int(packet[5])
		self._info("Added item {}".format(item_id))

	def add_coins(self, amount):
		amount = self._require_int("amount", amount)
		self._info("Adding {} coins...".format(amount))
		internal_room_id = self._internal_room_id
		self._internal_room_id = -1
		coins = self._coins
		room = self._room
		try:
			self._send_packet("s", "j#jr", 912, 0, 0)
			if self.next("jg") is None:
				self._error("Failed to add {} coins".format(amount))
			self._send_packet("z", "zo", amount)
			packet = self.next("zo")
			if packet is None:
				self._error("Failed to add {} coins".format(amount))
		finally:
			self._internal_room_id = internal_room_id
			self.room = room
		earn = int(packet[4]) - coins
		self._info("Added {} coins".format(earn))

	def add_stamp(self, stamp_id):
		stamp_id = self._require_int("stamp_id", stamp_id)
		self._info("Adding stamp {}...".format(stamp_id))
		self._send_packet("s", "st#sse", stamp_id)
		if self.next("aabs") is None:
			self._error("Failed to add stamp {}".format(stamp_id))
		self._info("Added stamp {}".format(stamp_id))

	def add_igloo(self, igloo_id):
		igloo_id = self._require_int("igloo_id", igloo_id)
		self._info("Adding igloo {}...".format(igloo_id))
		self._send_packet("s", "g#au", None, self._id, igloo_id)
		if self.next("au") is None:
			self._error("Failed to add igloo {}".format(igloo_id))
		self._info("Added igloo {}".format(igloo_id))

	def add_furniture(self, furniture_id):
		furniture_id = self._require_int("furniture_id", furniture_id)
		self._info("Adding furniture {}...".format(furniture_id))
		self._send_packet("s", "g#af", furniture_id)
		if self.next("af") is None:
			self._error("Failed to add furniture {}".format(furniture_id))
		self._info("Added furniture {}".format(furniture_id))

	def igloo_music(self, music_id):
		music_id = self._require_int("music_id", music_id)
		self._info("Setting igloo music to #{}...".format(music_id))
		self._send_packet("s", "g#um", None, self._id, music_id)
		if self.next("um") is None:
			self._error("Failed to set igloo music to {}".format(music_id))
		self._info("Set igloo music to #{}".format(music_id))

	def add_buddy(self, penguin_id):
		penguin = self.get_penguin(penguin_id)
		if penguin.id in self.buddies:
			self._error('"{}" is already buddy'.format(penguin.name))
		self._info('Sending buddy request to "{}"...'.format(penguin.name))
		self._send_packet("s", "b#br", penguin.id)
		if self.next("br") is None:
			self._error('Failed to send buddy request to "{}"'.format(penguin.name))
		self._info('Sent buddy request to "{}"'.format(penguin.name))

	def find_buddy(self, penguin_id):
		penguin = self.get_penguin(penguin_id)
		if penguin.id not in self.buddies:
			self._error('"{}" is not buddy'.format(penguin.name))
		if not self.buddies[penguin.id].online:
			self._error('"{}" is offline'.format(penguin.name))
		self._info('Finding buddy "{}"...'.format(penguin.name))
		self._send_packet("s", "b#bf", penguin.id)
		packet = self.next("bf")
		if packet is None:
			self._error('Failed to find buddy "{}"'.format(penguin.name))
		room_id = int(packet[4])
		self._info('Found buddy "{}"'.format(penguin.name))
		return room_id

	def follow(self, penguin_id, dx=0, dy=0):
		def equip(item_name):
			try:
				setattr(self, item_name, getattr(penguin, item_name))
			except ClientError:
				pass
		penguin = self.get_penguin(penguin_id)
		self._info('Following "{}"...'.format(penguin.name))
		if penguin.id == self._id:
			self._error("Cannot follow self")
		if penguin.id not in self._penguins:
			if penguin.id not in self.buddies or not self.buddies[penguin.id].online:
				self._error('Penguin "{}" not in room'.format(penguin.name))
			self.room = self.find_buddy(penguin.id)
		self._follow = (penguin.id, dx, dy)
		pool = ThreadPool()
		pool.map_async(equip, ["color", "head", "face", "neck", "body", "hand", "feet", "pin", "background"])
		try:
			self.walk(penguin.x + dx, penguin.y + dy)
		except ClientError:
			pass
		try:
			self.add_buddy(penguin.id)
		except ClientError:
			pass
		pool.close()
		pool.join()

	def unfollow(self):
		self._follow = None

	def logout(self):
		if not self._connected:
			return
		self._info("Logging out...")
		self._connected = False
		for handler in self._nexts:
			handler.cancel()
		if self._heartbeat_timer is not None:
			self._heartbeat_timer.cancel()
		try:
			self._sock.shutdown(socket.SHUT_RDWR)
		except socket.error:
			pass
		self._sock.close()
