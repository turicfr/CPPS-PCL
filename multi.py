import sys
import os
import json
import client
import login

def help(clients):
	return """HELP"""

def room(client, id):
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.Client.get_room_id(name)
		if not id:
			return "Room '" + name + "' not found"
	for client in clients:
		client.room = id

def igloo(client, id):
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.get_id(name)
		if not id:
			return "Penguin '" + name + "' not found"
	for client in clients:
		client.igloo = id

def color(clients, id):
	for client in clients:
		client.color = id

def head(clients, id):
	for client in clients:
		client.head = id

def face(clients, id):
	for client in clients:
		client.face = id

def neck(clients, id):
	for client in clients:
		client.neck = id

def body(clients, id):
	for client in clients:
		client.body = id

def hand(clients, id):
	for client in clients:
		client.hand = id

def feet(clients, id):
	for client in clients:
		client.feet = id

def pin(clients, id):
	for client in clients:
		client.pin = id

def background(clients, id):
	for client in clients:
		client.background = id

def walk(clients, x, y):
	for client, offset in zip(cliets, shape["offsets"]):
		client.walk(int(x) + int(offset["x"]), int(y) + int(offset["y"]))

def dance(clients):
	for client in clients:
		client.dance()

def wave(clients):
	for client in clients:
		client.wave()

def sit(clients, dir=None):
	if dir is None:
		for client in clients:
			client.sit()
	else:
		for client in clients:
			client.sit(dir)

def snowball(clients, x, y):
	for client in clients:
		client.snowball(x, y)

def say(clients, *params):
	message = ' '.join(params)
	for client in clients:
		client.say(message)

def joke(clients, params):
	if params:
		for client in clients:
			client.joke(params[0])
	else:
		print "An argument is required"

def emote(clients, id):
	for client in clients:
		client.emote(id)

def buy(clients, id):
	for client in clients:
		client.add_item(id)

def coins(clients, amount):
	for client in clients:
		client.add_item(amount)

def follow(clients, *params):
	name = ' '.join(params)
	for client, offset in zip(clients, shape["offsets"]):
		client.follow(name, int(offset["x"]), int(offset["y"]))

def unfollow(clients):
	for client in clients:
		client.unfollow()

def logout(clients):
	for client in clients:
		client.logout()
	sys.exit(0)

if __name__ == "__main__":
	cpps = raw_input("CPPS: ").lower()
	server = raw_input("Server: ").lower()
	login_ip, login_port, game_ip, game_port, magic = login.get_info(cpps, server)
	
	filename = os.path.join(os.path.dirname(__file__), "json/shapes.json")
	with open(filename) as file:
		data = json.load(file)
	shape = raw_input("Shape: ").lower()
	if not shape in data:
		sys.exit("Shape not found")
	shape = data[shape]
	
	count = len(shape["offsets"])
	clients = []
	for i in range(count):
		clients.append(client.Client(login_ip, login_port, game_ip, game_port, magic, False))
	
	print "Logins with " + str(count) + " penguin(s)..."
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	try:
		with open(filename) as file:
			data = json.load(file)
	except:
		data = {}
	
	if cpps in data:
		for user, password in data[cpps].items():
			error = clients[count - 1].connect(user, password, True)
			if error:
				print "Username: " + user
				if error == 603:
					login.remove_penguin(cpps, user, data)
			else:
				count -= 1
				if count == 0:
					print "All connected!"
					break
				else:
					print "Connected! (" + str(count) + " left)"
	
	i = 0
	while i < count:
		user = raw_input("Username: ").lower()
		password, encrypted = login.get_password(cpps, user)
		print "Connecting..."
		error = clients[i].connect(user, password)
		if not error:
			i += 1
			if i < count:
				print "Connected! (" + str(count - i) + " left)"
			else:
				print "All connected!"
	
	for client in clients:
		client.color = shape["color"]
		client.head = shape["head"]
		client.face = shape["face"]
		client.neck = shape["neck"]
		client.body = shape["body"]
		client.hand = shape["hand"]
		client.feet = shape["feet"]
		client.pin = shape["pin"]
		client.background = shape["background"]
	
	commands = {
		"help": help,
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
		"buy": buy,
		"coins": coins,
		"follow": follow,
		"unfollow": unfollow,
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
			try:
				print commands[name](clients, *params)
			except TypeError as e:
				print e.message
		elif name:
			print "command '" + name + "' doesn't exist"
