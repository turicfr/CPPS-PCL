import sys
import msvcrt
import hashlib
import os
import json
import client

def get_server(cpps):
	filename = os.path.join(os.path.dirname(__file__), "json/servers.json")
	with open(filename) as file:
		data = json.load(file)
	if not cpps in data:
		sys.exit("CPPS not found")
	return data[cpps]

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

	if remember and raw_input("Remember? [y/n] ") == "y":
		if not cpps in data:
			data[cpps] = {}
		data[cpps][user] = hashlib.md5(password).hexdigest()
		with open(filename, "w") as file:
			json.dump(data, file)
	return password, False

def remove_penguin(cpps, user, data = None):
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

def get_room_id(name):
	filename = os.path.join(os.path.dirname(__file__), "json/rooms.json")
	with open(filename) as file:
		data = json.load(file)
	for id in data:
		if data[id] == name:
			return int(id)
	return 0

def get_room_name(id):
	filename = os.path.join(os.path.dirname(__file__), "json/rooms.json")
	with open(filename) as file:
		data = json.load(file)
	if str(id) in data:
		return data[str(id)]
	return "Unknown"

def help(client, params):
	print """HELP"""

def log(client, params):
	client.log = not client.log
	if client.log:
		print "Log is on"
	else:
		print "Log is off"

def internal(client, params):
	print "Current: internal room id: " + client.internal_room_id

def id(client, params):
	if params:
		id = client.get_penguin_id(params[0])
	else:
		id = client.id
	if id:
		print "id: " + str(id)
	else:
		print "Penguin not found"

def room(client, params):
	if params:
		try:
			id = int(params[0])
		except ValueError:
			id = get_room_id(params[0])
			if not id:
				print "Room not found"
				return
		client.join_room(id)
	else:
		print "Current room: " + get_room_name(client.room_id)

def igloo(client, params):
	if params:
		try:
			id = int(params[0])
		except ValueError:
			id = client.get_penguin_id(params[0])
			if not id:
				print "Penguin not found"
				return
	else:
		id = client.id
	client.join_igloo(id)

def color(client, params):
	if params:
		client.update_color(params[0])
	else:
		print "Current color: " + str(client.penguins[client.id].clothes["color"])

def head(client, params):
	if params:
		client.update_head(params[0])
	else:
		print "Current head item: " + str(client.penguins[client.id].clothes["head"])

def face(client, params):
	if params:
		client.update_face(params[0])
	else:
		print "Current face item: " + str(client.penguins[client.id].clothes["face"])

def neck(client, params):
	if params:
		client.update_neck(params[0])
	else:
		print "Current neck item: " + str(client.penguins[client.id].clothes["neck"])

def body(client, params):
	if params:
		client.update_body(params[0])
	else:
		print "Current body item: " + str(client.penguins[client.id].clothes["body"])

def hand(client, params):
	if params:
		client.update_hand(params[0])
	else:
		print "Current hand item: " + str(client.penguins[client.id].clothes["hand"])

def feet(client, params):
	if params:
		client.update_feet(params[0])
	else:
		print "Current feet item: " + str(client.penguins[client.id].clothes["feet"])

def pin(client, params):
	if params:
		client.update_pin(params[0])
	else:
		print "Current pin: " + str(client.penguins[client.id].clothes["pin"])

def background(client, params):
	if params:
		client.update_background(params[0])
	else:
		print "Current background: " + str(client.penguins[client.id].clothes["background"])

def walk(client, params):
	if len(params) < 2:
		print "2 arguments are required"
	else:
		client.walk(params[0], params[1])

def dance(client, params):
	client.dance()

def wave(client, params):
	client.wave()

def sit(client, params):
	if params:
		client.sit(params[0])
	else:
		client.sit()

def snowball(client, params):
	if len(params) < 2:
		print "2 arguments are required"
	else:
		client.snowball(params[0], params[1])

def say(client, params):
	if params:
		client.say(' '.join(params))
	else:
		print "An argument is required"

def joke(client, params):
	if params:
		client.joke(params[0])
	else:
		print "An argument is required"

def emote(client, params):
	if params:
		client.emote(params[0])
	else:
		print "An argument is required"

def mail(client, params):
	if len(params) < 2:
		print "2 arguments are required"
	else:
		client.mail(params[0], params[1])

def buy(client, params):
	if params:
		client.add_item(params[0])
	else:
		print "An argument is required"

def coins(client, params):
	if params:
		client.add_coins(params[0])
	else:
		print "Current coins: " + str(client.coins)

def add_stamp(client, params):
	if params:
		client.add_stamp(params[0])
	else:
		print "An argument is required"

def add_igloo(client, params):
	if params:
		client.add_igloo(params[0])
	else:
		print "An argument is required"

def add_furniture(client, params):
	if params:
		client.add_furniture(params[0])
	else:
		print "An argument is required"

def buddy(client, params):
	if params:
		client.buddy(params[0])
	else:
		print "An argument is required"

def music(client, params):
	if params:
		client.music(params[0])
	else:
		print "An argument is required"

def follow(client, params):
	if params:
		if len(params) > 2:
			try:
				dx = int(params[-2])
				dy = int(params[-1])
				offset = True
			except ValueError:
				offset = False
			if offset:
				client.follow(' '.join(params[:-2]), dx, dy)
			else:
				client.follow(' '.join(params))
		else:
			client.follow(' '.join(params))
	elif client.followed:
		print "Currently following " + client.penguins[client.followed.id].name
	else:
		print "Currently not following"

def unfollow(client, params):
	client.unfollow()

def logout(client, params):
	client.logout()
	sys.exit(0)

if __name__ == "__main__":
	cpps = "cpg"
	data = get_server(cpps)
	user = raw_input("Username: ").lower()
	password, encrypted = get_password(cpps, user)
	server = raw_input("Server: ").lower()
	
	ip = data["ip"]
	login_port = data["login"]
	game_port = data["servers"]
	if not server in game_port:
		sys.exit("Server not found")
	game_port = game_port[server]
	if "magic" in data:
		magic = data["magic"]
	else:
		magic = None
	
	client = client.Client(ip, login_port, game_port, True, magic)
	if not client.log:
		print "Connecting..."
	error = client.connect(user, password, encrypted)
	if error:
		if error == 603:
			remove_penguin(cpps, user)
		sys.exit("Failed to connect")
	print "Connected!"
	commands = {
		"help": help,
		"log": log,
		"internal": internal,
		"id": id,
		"room": room,
		"igloo": igloo,
		"color": color,
		"head": head,
		"face": face,
		"neck": neck,
		"body": body,
		"hand": hand,
		"feet": feet,
		"pin": pin,
		"background": background,
		"walk": walk,
		"dance": dance,
		"wave": wave,
		"sit": sit,
		"snowball": snowball,
		"say": say,
		"joke": joke,
		"emote": emote,
		"mail": mail,
		"buy": buy,
		"coins": coins,
		"stamp": add_stamp,
		"add_igloo": add_igloo,
		"furniture": add_furniture,
		"buddy": buddy,
		"music": music,
		"follow": follow,
		"unfollow": unfollow,
		"logout": logout
	}
	while True:
		print ">>>",
		cmd = raw_input().split(' ')
		name = cmd[0]
		params = cmd[1:]
		if name in commands:
			commands[name](client, params)
		else:
			print "command '" + name + "' doesn't exist"
