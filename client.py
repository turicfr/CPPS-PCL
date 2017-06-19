import socket
import hashlib
import re
import os
import json
import threading

class Penguin:
	def __init__(self, id, name, clothes, x, y):
		self.id = id
		self.name = name
		self.clothes = clothes
		self.x = x
		self.y = y
	
	@classmethod
	def from_player(cls, player):
		player = player.split('|')
		id = player[0]
		name = player[1]
		clothes = {}
		# ??? = player[2]
		info = ["color", "head", "face", "neck", "body", "hand", "feet", "pin", "background"]
		for i in range(len(info)):
			if player[i + 3]:
				clothes[info[i]] = int(player[i + 3])
		x = int(player[12])
		y = int(player[13])
		return cls(id, name, clothes, x, y)

class Client:
	def __init__(self, ip, login_port, game_port, log = False):
		self.ip = ip
		self.login_port = login_port
		self.game_port = game_port
		self.log = log
		self.buf = ""
		self.internal_room_id = "-1"
		self.penguins = {}
		self.followed = None

	def _swapped_md5(self, password):
		hash = hashlib.md5(password).hexdigest()
		swap = hash[16:32] + hash[0:16]
		return swap

	def _send(self, data):
		if self.log:
			print "# SEND: " + str(data)
		self.sock.send(data + chr(0))

	def _receive(self):
		while not chr(0) in self.buf:
			self.buf += self.sock.recv(4096)
		i = self.buf.index(chr(0)) + 1
		m = self.buf[:i]
		self.buf = self.buf[i:]
		if self.log:
			print "# RECEIVE: " + str(m)
		return m

	def _packet(self):
		buf = self._receive()
		if buf.startswith("%"):
			packet = buf.split('%')
			if packet[2] == "e":
				self._error(packet)
				return None
			return packet
		raise Exception("Invalid packet")

	def _error(self, packet):
		filename = os.path.join(os.path.dirname(__file__), "json/errors.json")
		with open(filename) as file:
			data = json.load(file)
		code = packet[4]
		print data[code]

	def _ver_check(self, ver = 153):
		if self.log:
			print "Sending 'verChk' request..."
		self._send('<msg t="sys"><body action="verChk" r="0"><ver v="' + str(ver) + '"/></body></msg>')
		buf = self._receive()
		if 'apiOK' in buf:
			if self.log:
				print "Received 'apiOK' response."
			return True
		if 'apiKO' in buf:
			if self.log:
				print "Received 'apiKO' response."
			return False
		raise Exception("Invalid response")

	def _key(self):
		if self.log:
			print "Sending rndK request..."
		self._send('<msg t="sys"><body action="rndK" r="-1"></body></msg>')
		buf = self._receive()
		if 'rndK' in buf:
			key = re.search("<k>(<!\[CDATA\[)?(.*?)(\]\]>)?<\/k>", buf).group(2)
			if self.log:
				print "Received key: " + key
			return key
		raise Exception("Invalid response")

	def _login(self, user, password, ver):
		if self.log:
			print "Logging in..."
		self._ver_check(ver)
		rndk = self._key()
		hash = self._swapped_md5(self._swapped_md5(password).upper() + rndk + "Y(02.>'H}t\":E1")
		self._send('<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[' + user + ']]></nick><pword><![CDATA[' + hash + ']]></pword></login></body></msg>')
		packet = self._packet()
		if not packet:
			return None
		while packet[2] != 'l':
			packet = self._packet()
			if not packet:
				return None
		if self.log:
			print "Logged in."
		return packet

	def _join_server(self, user, login_key, ver):
		if self.log:
			print "Joining server..."
		self._ver_check(ver)
		rndk = self._key()
		hash = self._swapped_md5(login_key + rndk) + login_key
		self._send('<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[' + user + ']]></nick><pword><![CDATA[' + hash + ']]></pword></login></body></msg>')
		packet = self._packet()
		if packet and packet[2] == 'l':
			self._send("%xt%s%j#js%" + self.internal_room_id + "%" + self.id + "%" + login_key + "%en%")
			packet = self._packet()
			if packet and packet[2] == "js":
				if self.log:
					print "Joined server."
				return packet
		return None
		
	def _get_id(self, name):
		for penguin in self.penguins.values():
			if penguin.name == name:
				return penguin.id
		return None
		
	def _game(self):
		thread = threading.Thread(target = self._heartbeat)
		thread.start()
		while True:
			packet = self._packet()
			if not packet:
				return
			op = packet[2]
			if op == "lp" or op == "ap":
				penguin = Penguin.from_player(packet[4])
				self.penguins[penguin.id] = penguin
			elif op == "jr":
				self.internal_room_id = packet[3]
				self.penguins.clear()
				room = int(packet[4])
				for i in packet[5:-1]:
					penguin = Penguin.from_player(i)
					self.penguins[penguin.id] = penguin
			elif op == "rp":
				id = packet[4]
				penguin = self.penguins.pop(id)
				if self.followed and id == self.followed["id"]:
					self._send("%xt%s%b#bf%" + self.internal_room_id + "%" + id + "%")
			elif op == "bf":
				room = packet[4]
				self.room(room)
			elif op == "sp":
				id = packet[4]
				penguin = self.penguins[id]
				penguin.x = int(packet[5])
				penguin.y = int(packet[6])
				if self.followed and id == self.followed["id"]:
					self.walk(penguin.x + self.followed["x"], penguin.y + self.followed["y"])
			elif op == "sm":
				id = packet[4]
				message = packet[5]
				if self.followed and id == self.followed["id"]:
					self.say(message, False)
			elif op == "ss":
				id = packet[4]
				message = packet[5]
				if self.followed and id == self.followed["id"]:
					self.say(message, True)
			elif op == "sj":
				id = packet[4]
				joke = packet[5]
				if self.followed and id == self.followed["id"]:
					self.joke(joke)
			elif op == "se":
				id = packet[4]
				emote = packet[5]
				if self.followed and id == self.followed["id"]:
					self.emote(emote)
			elif op == "sb":
				id = packet[4]
				x = packet[5]
				y = packet[6]
				if self.followed and id == self.followed["id"]:
					self.snowball(x, y)
			elif self.log:
				print "# UNKNOWN OPCODE: " + op
				
	def _heartbeat(self):
		threading.Timer(600, self._heartbeat)
		self._send("%xt%s%u#h%1%")

	def connect(self, user, password, ver = 153):
		if self.log:
			print "Connecting to " + self.ip + ":" + str(self.login_port) + "..."
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.ip, self.login_port))
			
		buf = self._login(user, password, ver)
		if buf:
			self.id = buf[4]
			login_key = buf[5]
			
			if self.log:
				print "Connecting to " + self.ip + ":" + str(self.game_port) + "..."
			
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((self.ip, self.game_port))
			
			buf = self._join_server(user, login_key, ver)
			if buf:
				thread = threading.Thread(target = self._game)
				thread.start()
				return True
		return False
		
	def room(self, id, x = 0, y = 0):
		if self.log:
			print "going to room " + str(id) + "..."
		self._send("%xt%s%j#jr%" + self.internal_room_id + "%" + id + "%" + str(x) + "%" + str(y) + "%")
		
	def update_color(self, id):
		if self.log:
			print "changing color to " + str(id) + "..."
		self._send("%xt%s%s#upc%" + self.internal_room_id + "%" + str(id) + "%")

	def update_head(self, id):
		if self.log:
			print "changing head item to " + str(id) + "..."
		self._send("%xt%s%s#uph%" + self.internal_room_id + "%" + str(id) + "%")

	def update_face(self, id):
		if self.log:
			print "changing face item to " + str(id) + "..."
		self._send("%xt%s%s#upf%" + self.internal_room_id + "%" + str(id) + "%")

	def update_neck(self, id):
		if self.log:
			print "changing neck item to " + str(id) + "..."
		self._send("%xt%s%s#upn%" + self.internal_room_id + "%" + str(id) + "%")

	def update_body(self, id):
		if self.log:
			print "changing body item to " + str(id) + "..."
		self._send("%xt%s%s#upb%" + self.internal_room_id + "%" + str(id) + "%")

	def update_hand(self, id):
		if self.log:
			print "changing hand item to " + str(id) + "..."
		self._send("%xt%s%s#upa%" + self.internal_room_id + "%" + str(id) + "%")

	def update_feet(self, id):
		if self.log:
			print "changing feet item to " + str(id) + "..."
		self._send("%xt%s%s#upe%" + self.internal_room_id + "%" + str(id) + "%")

	def update_pin(self, id):
		if self.log:
			print "changing pin to " + str(id) + "..."
		self._send("%xt%s%s#upl%" + self.internal_room_id + "%" + str(id) + "%")

	def update_background(self, id):
		if self.log:
			print "changing background to " + str(id) + "..."
		self._send("%xt%s%s#upp%" + self.internal_room_id + "%" + str(id) + "%")
		
	def walk(self, x, y):
		if self.log:
			print "walking to (" + str(x) + ", " + str(y) + ")..."
		self._send("%xt%s%u#sp%" + self.id + "%" + str(x) + "%" + str(y) + "%")
		
	def _action(self, id):
		self._send("%xt%s%u#sa%" + self.internal_room_id + "%" + str(id) + "%")
		
	def _frame(self, id):
		self._send("%xt%s%u#sf%" + self.internal_room_id + "%" + str(id) + "%")
		
	def dance(self):
		if self.log:
			print "dancing..."
		self._frame(26)

	def wave(self):
		if self.log:
			print "waving..."
		self._action(25)
		
	def sit(self, dir):
		if self.log:
			print "sitting..."
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
		if dir in dirs:
			self._frame(dirs[dir])
		else:
			self._frame(dirs["s"])

	def snowball(self, x, y):
		if self.log:
			print "throwing snowball to (" + str(x) + ", " + str(y) + ")..."
		self._send("%xt%s%u#sb%" + self.internal_room_id + "%" + str(x) + "%" + str(y) + "%")

	def say(self, message, safe = False):
		if self.log:
			print "saying '" + message + "'..."
		if safe:
			self._send("%xt%s%u#ss%" + self.internal_room_id + "%" + message + "%")
		else:
			self._send("%xt%s%m#sm%" + self.internal_room_id + "%" + self.id + "%" + message + "%")

	def joke(self, joke):
		if self.log:
			print "saying joke " + str(joke) + "..."
		self._send("%xt%s%u#sj%" + self.id + "%" + str(joke) + "%")
		
	def emote(self, emote):
		if self.log:
			print "saying emote " + str(emote) + "..."
		self._send("%xt%s%u#se%" + self.internal_room_id + "%" + str(emote) + "%")
		
	def add_item(self, id):
		if self.log:
			print "adding item " + str(id) + "..."
		self._send("%xt%s%i#ai%" + self.internal_room_id + "%" + str(id) + "%")

	def follow(self, name, offset_x = 0, offset_y = 0):
		if self.log:
			print "following " + name + "..."
		id = self._get_id(name)
		if id:
			self.followed = {"id": id, "x": offset_x, "y": offset_y}
			penguin = self.penguins[id]
			self.walk(penguin.x + offset_x, penguin.y + offset_y)

	def unfollow(self):
		if self.log:
			print "unfollowing..."
		self.followed = None

	def logout(self):
		if self.log:
			print "logging out..."
		self.sock.close()