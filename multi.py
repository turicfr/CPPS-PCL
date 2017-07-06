import sys
import os
import json
import client
import login

def help(clients, params):
	print """HELP"""

def room(clients, params):
	if params:
		try:
			id = int(params[0])
		except ValueError:
			id = login.get_room_id(params[0])
			if not id:
				print "Room not found"
				return
		for client in clients:
			client.go_to_room(id)
	else:
		print "An argument is required"

def color(clients, params):
	if params:
		for client in clients:
			client.update_color(params[0])
	else:
		print "An argument is required"

def head(clients, params):
	if params:
		for client in clients:
			client.update_head(params[0])
	else:
		print "An argument is required"

def face(clients, params):
	if params:
		for client in clients:
			client.update_face(params[0])
	else:
		print "An argument is required"

def neck(clients, params):
	if params:
		for client in clients:
			client.update_neck(params[0])
	else:
		print "An argument is required"

def body(clients, params):
	if params:
		for client in clients:
			client.update_body(params[0])
	else:
		print "An argument is required"

def hand(clients, params):
	if params:
		for client in clients:
			client.update_hand(params[0])
	else:
		print "An argument is required"

def feet(clients, params):
	if params:
		for client in clients:
			client.update_feet(params[0])
	else:
		print "An argument is required"

def pin(clients, params):
	if params:
		for client in clients:
			client.update_pin(params[0])
	else:
		print "An argument is required"

def background(clients, params):
	if params:
		for client in clients:
			client.update_background(params[0])
	else:
		print "An argument is required"

def walk(clients, params):
	if len(params) < 2:
		print "2 arguments are required"
	else:
		for i in range(len(clients)):
			client = clients[i]
			offset = shape["offsets"][i]
			client.walk(int(params[0]) + int(offset["x"]), int(params[1]) + int(offset["y"]))

def dance(clients, params):
	for client in clients:
		client.dance()

def wave(clients, params):
	for client in clients:
		client.wave()

def sit(clients, params):
	if params:
		for client in clients:
			client.sit(params[0])
	else:
		for client in clients:
			client.sit()

def snowball(clients, params):
	if len(params) < 2:
		print "2 arguments are required"
	else:
		for client in clients:
			client.snowball(params[0], params[1])

def say(clients, params):
	if params:
		message = ' '.join(params)
		for client in clients:
			client.say(message)
	else:
		print "An argument is required"

def joke(clients, params):
	if params:
		for client in clients:
			client.joke(params[0])
	else:
		print "An argument is required"

def emote(clients, params):
	if params:
		for client in clients:
			client.emote(params[0])
	else:
		print "An argument is required"

def buy(clients, params):
	if params:
		for client in clients:
			client.add_item(params[0])
	else:
		print "An argument is required"

def follow(clients, params):
	if params:
		name = ' '.join(params)
		for i in range(len(clients)):
			client = clients[i]
			offset = shape["offsets"][i]
			client.follow(name, int(offset["x"]), int(offset["y"]), True)
	else:
		print "An argument is required"

def unfollow(clients, params):
	for client in clients:
		client.unfollow()

def logout(clients, params):
	for client in clients:
		client.logout()
	sys.exit(0)

if __name__ == "__main__":
	cpps = "cpr"
	data = login.get_server(cpps)
	server = raw_input("Server: ").lower()
	ip = data["ip"]
	login_port = data["login"]
	game_port = data["servers"]
	if not server in game_port:
		sys.exit("Server not found")
	game_port = game_port[server]
	
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
		clients.append(client.Client(ip, login_port, game_port))
	
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
					del data[cpps][user]
					with open(filename, "w") as file:
						json.dump(data, file)
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
	
	commands = {
		"help": help,
		"room": room,
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
			commands[name](clients, params)
		else:
			print "command '" + name + "' doesn't exist"