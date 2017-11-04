import sys
import msvcrt
import hashlib
import os
import json
import logging
import client as pcl

def get_server(cpps, server):
	filename = os.path.join(os.path.dirname(__file__), "json/.servers.json")
	with open(filename) as file:
		data = json.load(file)
	if not cpps in data:
		sys.exit("CPPS not found")
	if not server in data[cpps]["servers"]:
		sys.exit("Server not found")

	if "ip" in data[cpps]:
		login_ip = game_ip = data[cpps]["ip"]
		login_port = data[cpps]["login"]
		game_port = data[cpps]["servers"][server]
	else:
		login_ip, login_port = data[cpps]["login"].split(':')
		login_port = int(login_port)
		game_ip, game_port = data[cpps]["servers"][server].split(':')
		game_port = int(game_port)
	magic = data[cpps]["magic"] if "magic" in data[cpps] else None
	
	return login_ip, login_port, game_ip, game_port, magic

def get_client(cpps, server):
	login_ip, login_port, game_ip, game_port, magic = get_server(cpps, server)
	logger = logging.getLogger()
	logger.setLevel(logging.NOTSET)
	handler = logging.StreamHandler(sys.stdout)
	logger.addHandler(handler)
	return pcl.Client(login_ip, login_port, game_ip, game_port, magic, logger)

def get_password(cpps, user, remember = True):
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	try:
		with open(filename) as file:
			data = json.load(file)
	except:
		data = {}
	if cpps in data and user in data[cpps]:
		return data[cpps][user], True
	
	print "Password: ",
	password = ""
	special = False
	while True:
		c = msvcrt.getch()
		if special:
			special = False
		elif c == '\r' or c == '\n':
			break
		elif c == '\b':
			if len(password):
				sys.stdout.write("\b \b")
				password = password[:-1]
		elif c == '\xe0':
			special = True
		elif 32 <= ord(c) < 127:
			sys.stdout.write('*')
			password += c
	print ""

	if remember and raw_input("Remember? [y/N] ") == "y":
		if not cpps in data:
			data[cpps] = {}
		data[cpps][user] = hashlib.md5(password).hexdigest()
		with open(filename, "w") as file:
			json.dump(data, file)
	return password, False

def remove_penguin(cpps, user, data=None):
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	if not data:
		try:
			with open(filename) as file:
				data = json.load(file)
		except:
			return False
	if cpps in data and user in data[cpps]:
		print "Removing " + user + "..."
		del data[cpps][user]
		with open(filename, "w") as file:
			json.dump(data, file)
		return True
	return False

def login():
	cpps = raw_input("CPPS: ").lower()
	user = raw_input("Username: ").lower()
	password, encrypted = get_password(cpps, user)
	server = raw_input("Server: ").lower()
	client = get_client(cpps, server)
	try:
		client.connect(user, password, encrypted)
	except client.ClientError as e:
		if e.code == 603:
			remove_penguin(cpps, user)
		sys.exit("Failed to connect")
	print "Connected!"
	return client

def help(client):
	return """HELP"""

def log(client, level=None):
	if level is None:
		if client.logger.level:
			msg = "all"
			level = logging.NOTSET
		else:
			msg = "error"
			level = logging.ERROR
	else:
		msg = level
		if level == "all":
			level = logging.NOTSET
		if level == "debug":
			level = logging.DEBUG
		elif level == "info":
			level = logging.INFO
		elif level == "warning":
			level = logging.WARNING
		elif level == "error":
			level = logging.ERROR
		elif level == "cricital":
			level = logging.CRICITAL
		else:
			return "Unknown logging level '" + level + "'"
	client.logger.setLevel(level)
	return "Logging " + msg + " messages"

def internal(client):
	return "Current internal room id: " + str(client.internal_room_id)

def id(client, name=None):
	if name is None:
		id = client.id
	else:
		id = client.get_id(name)
		if not id:
			return "Penguin '" + name + "' not found"
	return "ID: " + str(id)

def name(client, id=None):
	if id is None:
		name = client.name
	elif id in client.penguins:
		name = client.penguins[id].name
	else:
		return "Penguin #" + str(id) + " not found"
	return "Name: " + name

def room(client, id=None):
	if id is None:
		return "Current room: " + client.get_room_name(client.room)
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.get_room_id(name)
		if not id:
			return "Room '" + name + "' not found"
	client.room = id
	
def igloo(client, id=None):
	if id is None:
		id = client.id
	else:
		try:
			id = int(id)
		except ValueError:
			name = id
			id = client.get_id(name)
			if not id:
				return "Penguin '" + name + "' not found"
	client.igloo = id

def penguins(client):
	return '\n'.join(penguin.name for id, penguin in client.penguins.iteritems())

def color(client, id=None):
	if id is None:
		return "Current color: " + str(client.color)
	else:
		client.color = id

def head(client, id=None):
	if id is None:
		return "Current head item: " + str(client.head)
	else:
		client.head = id

def face(client, id=None):
	if id is None:
		return "Current face item: " + str(client.face)
	else:
		client.face = id

def neck(client, id=None):
	if id is None:
		return "Current neck item: " + str(client.neck)
	else:
		client.neck = id

def body(client, id=None):
	if id is None:
		return "Current body item: " + str(client.body)
	else:
		client.body = id

def hand(client, id=None):
	if id is None:
		return "Current hand item: " + str(client.hand)
	else:
		client.hand = id

def feet(client, id=None):
	if id is None:
		return "Current feet item: " + str(client.feet)
	else:
		client.feet = id

def pin(client, id=None):
	if id is None:
		return "Current pin: " + str(client.pin)
	else:
		client.pin = id

def background(client, id=None):
	if id is None:
		return "Current background: " + str(client.background)
	else:
		client.background = id

def inventory(client):
	return '\n'.join(client.inventory)

def stamps(client):
	return '\n'.join(client.stamps)

def say(client, *params):
	client.say(' '.join(params))

def mail(client, *params):
	if len(params) > 1:
		postcard = params[0]
		name = ' '.join(params[1:])
		id = client.get_id(name)
		if not id:
			return "Penguin '" + name + "' not found"
		client.mail(id, postcard)

def coins(client, amount=None):
	if amount is None:
		return "Current coins: " + str(client.coins)
	else:
		client.add_coins(amount)

def buddy(client, *params):
	name = ' '.join(params)
	id = client.get_id(name)
	if not id:
		return "Penguin '" + name + "' not found"
	client.buddy(id)

def follow(client, *params):
	if params:
		offset = False
		if len(params) > 2:
			try:
				dx = int(params[-2])
				dy = int(params[-1])
				params = params[:-2]
				offset = True
			except ValueError:
				pass
		name = ' '.join(params)
		id = client.get_id(name)
		if not id:
			return "Penguin '" + name + "' not found"
		if offset:
			client.follow(id, dx, dy)
		else:
			client.follow(id)
		return None
	elif client._follow:
		return "Currently following '" + client.penguins[client._follow[0]].name + "'"
	return "Currently not following"

def logout(client):
	client.logout()
	sys.exit(0)

if __name__ == "__main__":
	client = login()
	commands = {
		"help": help,
		"log": log,
		"internal": internal,
		"id": id,
		"name": name,
		"room": room,
		"igloo": igloo,
		"penguins": penguins,
		"color": color,
		"head": head,
		"face": face,
		"neck": neck,
		"body": body,
		"hand": hand,
		"feet": feet,
		"pin": pin,
		"background": background,
		"inventory": inventory,
		"stamps": stamps,
		"walk": client.walk,
		"dance": client.dance,
		"wave": client.wave,
		"sit": client.sit,
		"snowball": client.snowball,
		"say": say,
		"joke": client.joke,
		"emote": client.emote,
		"mail": mail,
		"buy": client.add_item,
		"ai": client.add_item,
		"coins": coins,
		"ac": client.add_coins,
		"stamp": client.add_stamp,
		"add_igloo": client.add_igloo,
		"add_furniture": client.add_furniture,
		"music": client.igloo_music,
		"buddy": buddy,
		"follow": follow,
		"unfollow": client.unfollow,
		"logout": logout,
		"exit": logout,
		"quit": logout
	}
	while True:
		print ">>>",
		cmd = raw_input().split(' ')
		name = cmd[0]
		params = cmd[1:]
		if name in commands:
			function = commands[name]
			try:
				if hasattr(function, "__self__"):
					function(*params)
				else:
					msg = function(client, *params)
					if msg:
						print msg
			except TypeError as e:
				if function.__name__ + "() takes" not in e.message:
					raise
				print e.message
			except pcl.ClientError as e:
				print e.message
		elif name:
			print "command '" + name + "' doesn't exist"
