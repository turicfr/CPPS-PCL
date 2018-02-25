import os
import sys
import json
import logging
import client as pcl
import login
try:
	import readline
except ImportError:
	pass

def help(clients):
	return """HELP"""

def room(client, id):
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.Client.get_room_id(name)
		if not id:
			return "Room '{}' not found".format(name)
	for client in clients:
		client.room = id

def igloo(client, id):
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.get_id(name)
		if not id:
			return "Penguin '{}' not found".format(name)
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

def add_item(clients, id):
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

def main():
	if "-r" in sys.argv:
		remember = sys.argv.pop(sys.argv.index("-r") + 1)
		sys.argv.remove("-r")
		if remember == "yes":
			remember = True
		elif remember == "no":
			remember = False
		elif remember == "ask":
			remember = None
		else:
			sys.exit("Unknown remember option: '{}'".format(remember))
	else:
		remember = None

	argc = len(sys.argv)
	if argc > 1:
		cpps = sys.argv[1].lower()
	else:
		cpps = raw_input("CPPS: ").lower()

	filename = os.path.join(os.path.dirname(__file__), "json/shapes.json")
	with open(filename) as file:
		data = json.load(file)
	if argc > 3:
		shape = sys.argv[3]
	else:
		shape = raw_input("Shape: ").lower()
	if not shape in data:
		sys.exit("Shape not found")
	shape = data[shape]

	if argc > 2:
		server = sys.argv[2]
	else:
		server = raw_input("Server: ").lower()
	login_ip, login_port, game_ip, game_port, magic, single_quotes = login.get_server(cpps, server)
	
	logger = logging.getLogger()
	logger.addHandler(logging.NullHandler())
	count = len(shape["offsets"])
	clients = []
	for i in range(count):
		clients.append(pcl.Client(login_ip, login_port, game_ip, game_port, magic, single_quotes, logger))
	
	print "Logins with {} penguin(s)...".format(count)
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	try:
		with open(filename) as file:
			data = json.load(file)
	except:
		data = {}
	
	if cpps in data:
		for user, password in data[cpps].iteritems():
			try:
				clients[count - 1].connect(user, password, True)
			except pcl.ClientError as e:
				print "Username: {}".format(user)
				if e.code == 603:
					login.remove_penguin(cpps, user, data)
				continue
			count -= 1
			if count == 0:
				break
			print "Connected! ({} left)".format(count)
	
	i = 0
	while i < count:
		user = raw_input("Username: ").lower()
		password, encrypted = login.get_password(cpps, user, remember)
		print "Connecting..."
		try:
			clients[i].connect(user, password)
		except pcl.ClientError as e:
			continue
		i += 1
		if i < count:
			print "Connected! ({} left)".format(count - i)
	print "All connected!"
	
	for client in clients:
		if "color" in shape:
			client.color = shape["color"]
		if "head" in shape:
			client.head = shape["head"]
		if "face" in shape:
			client.face = shape["face"]
		if "neck" in shape:
			client.neck = shape["neck"]
		if "body" in shape:
			client.body = shape["body"]
		if "hand" in shape:
			client.hand = shape["hand"]
		if "feet" in shape:
			client.feet = shape["feet"]
		if "pin" in shape:
			client.pin = shape["pin"]
		if "background" in shape:
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
		"buy": add_item,
		"ai": add_item,
		"coins": coins,
		"follow": follow,
		"unfollow": unfollow,
		"logout": logout,
		"exit": logout,
		"quit": logout
	}
	while True:
		try:
			command = raw_input(">>> ").split(' ')
		except KeyboardInterrupt:
			print
			continue
		except EOFError:
			logout(clients)
		command, params = command[0], command[1:]
		if command in commands:
			try:
				msg = commands[command](clients, *params)
				if msg is not None:
					print msg
			except TypeError as e:
				if function.__name__ + "() takes" not in e.message:
					raise
				print e.message
			except pcl.ClientError as e:
				print e.message
		elif command:
			print "command '{}' doesn't exist".format(name)

if __name__ == "__main__":
	main()
