import os
import sys
import hashlib
import json
import logging
from getpass import getpass
from client import Client, ClientError
try:
	import readline
except ImportError:
	readline = None

class LoginError(Exception):
	def __init__(self, message=""):
		super(LoginError, self).__init__(message)

def get_json(filename):
	filename = os.path.join(os.path.dirname(__file__), "json", filename + ".json")
	try:
		with open(filename) as file:
			return json.load(file)
	except IOError:
		return {}

def set_json(filename, data):
	filename = os.path.join(os.path.dirname(__file__), "json", filename + ".json")
	try:
		with open(filename, "w") as file:
			json.dump(data, file)
	except IOError:
		return False
	return True

def get_remember():
	if "-r" in sys.argv:
		index = sys.argv.index("-r")
		remember = sys.argv.pop(index + 1)
		sys.argv.pop(index)
		if remember == "yes":
			return True
		if remember == "no":
			return False
		if remember == "ask":
			return None
		raise LoginError('Unknown remember option: "{}"'.format(remember))
	return None

def complete(options):
	def complete_inner(text, state):
		line = readline.get_line_buffer()
		return [option for option in options if option.startswith(line)][state]
	return complete_inner

def get_input(prompt=None, options=None):
	if readline is not None and options is not None:
		completer_delims = readline.get_completer_delims()
		completer = readline.get_completer()

		readline.set_completer_delims("")
		readline.parse_and_bind("tab: complete")
		readline.set_completer(complete(options))
	try:
		return raw_input() if prompt is None else raw_input(prompt)
	finally:
		if readline is not None and options is not None:
			readline.set_completer_delims(completer_delims)
			readline.set_completer(completer)

def get_cpps(servers, cpps=None):
	if cpps is None:
		cpps = get_input("CPPS: ", servers.keys())
	cpps = cpps.lower()
	if cpps not in servers:
		raise LoginError("CPPS not found")
	return cpps

def get_user(penguins, cpps, user=None):
	if user is None:
		user = get_input("Username: ", penguins.get(cpps, {}).keys())
	user = user.lower()
	return user

def get_password(penguins, cpps, user, remember=None):
	if cpps in penguins and user in penguins[cpps]:
		return penguins[cpps][user], True
	password = getpass("Password: ")
	if remember is None:
		remember = get_input("Remember? [y/N] ", ["y", "N"]) == "y"
	if remember:
		if cpps not in penguins:
			penguins[cpps] = {}
		penguins[cpps][user] = hashlib.md5(password).hexdigest()
		set_json("penguins", penguins)
	return password, False

def get_server(servers, cpps, server=None):
	if server is None:
		server = get_input("Server: ", servers[cpps]["servers"].keys())
	server = server.lower()
	if server not in servers[cpps]["servers"]:
		raise LoginError("Server not found")
	return server

def get_client(servers, cpps, server, logger=None):
	if "ip" in servers[cpps]:
		login_ip = game_ip = servers[cpps]["ip"]
		login_port = servers[cpps]["login"]
		game_port = servers[cpps]["servers"][server]
	else:
		login_ip, login_port = servers[cpps]["login"].split(":")
		login_port = int(login_port)
		game_ip, game_port = servers[cpps]["servers"][server].split(":")
		game_port = int(game_port)
	magic = servers[cpps].get("magic")
	single_quotes = servers[cpps].get("single_quotes")
	return Client(login_ip, login_port, game_ip, game_port, magic, single_quotes, logger)

def get_penguin(cpps=None, server=None, user=None, remember=None):
	servers = get_json("servers")
	penguins = get_json("penguins")

	try:
		cpps = get_cpps(servers, cpps)
		user = get_user(penguins, cpps, user)
		password, encrypted = get_password(penguins, cpps, user, remember)
		server = get_server(servers, cpps, server)
	except KeyboardInterrupt:
		raise LoginError()

	client = get_client(servers, cpps, server)
	return cpps, server, user, password, encrypted, client

def remove_penguin(cpps, user, penguins=None):
	if penguins is None:
		penguins = get_json("penguins")
	if cpps in penguins and user in penguins[cpps]:
		print "Removing {}...".format(user)
		del penguins[cpps][user]
		set_json("penguins", penguins)

def login():
	remember = get_remember()
	argc = len(sys.argv)
	cpps = sys.argv[1] if argc > 1 else None
	server = sys.argv[2] if argc > 2 else None
	user = sys.argv[3] if argc > 3 else None
	cpps, server, user, password, encrypted, client = get_penguin(cpps, server, user, remember)

	try:
		client.connect(user, password, encrypted)
	except ClientError as e:
		if e.code == 101 or e.code == 603:
			remove_penguin(cpps, user)
		raise LoginError("Failed to connect")
	print "Connected!"
	return client

def help(client):
	return """HELP"""

def log(client, level=None):
	if level is None:
		if client.logger.level:
			name = "all"
			level = logging.NOTSET
		else:
			name = "error"
			level = logging.ERROR
	else:
		name = level
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
		elif level == "critical":
			level = logging.CRITICAL
		else:
			return 'Unknown logging level "{}"'.format(level)
	client.logger.setLevel(level)
	return "Logging {} messages".format(name)

def internal(client):
	return "Current internal room id: {}".format(client.internal_room_id)

def id(client, name=None):
	if name is None:
		id = client.id
	else:
		id = client.get_id(name)
		if not id:
			return 'Penguin "{}" not found'.format(name)
	return "ID: {}".format(id)

def name(client, id=None):
	if id is None:
		name = client.name
	elif id in client.penguins:
		name = client.penguins[id].name
	else:
		return "Penguin #{} not found".format(id)
	return "Name: {}".format(name)

def room(client, id=None):
	if id is None:
		return "Current room: {}".format(client.get_room_name(client.room))
	try:
		id = int(id)
	except ValueError:
		name = id
		id = client.get_room_id(name)
		if not id:
			return 'Room "{}" not found'.format(name)
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
				return 'Penguin "{}" not found'.format(name)
	client.igloo = id

def penguins(client):
	return "\n".join(penguin.name for id, penguin in client.penguins.iteritems())

def color(client, id=None):
	if id is None:
		return "Current color: {}".format(client.color)
	else:
		client.color = id

def head(client, id=None):
	if id is None:
		return "Current head item: {}".format(client.head)
	else:
		client.head = id

def face(client, id=None):
	if id is None:
		return "Current face item: {}".format(client.face)
	else:
		client.face = id

def neck(client, id=None):
	if id is None:
		return "Current neck item: {}".format(client.neck)
	else:
		client.neck = id

def body(client, id=None):
	if id is None:
		return "Current body item: {}".format(client.body)
	else:
		client.body = id

def hand(client, id=None):
	if id is None:
		return "Current hand item: {}".format(client.hand)
	else:
		client.hand = id

def feet(client, id=None):
	if id is None:
		return "Current feet item: {}".format(client.feet)
	else:
		client.feet = id

def pin(client, id=None):
	if id is None:
		return "Current pin: {}".format(client.pin)
	else:
		client.pin = id

def background(client, id=None):
	if id is None:
		return "Current background: {}".format(client.background)
	else:
		client.background = id

def inventory(client):
	return "\n".join(str(id) for id in client.inventory)

def stamps(client):
	return "\n".join(client.stamps)

def say(client, *params):
	client.say(" ".join(params))

def mail(client, *params):
	if len(params) > 1:
		postcard = params[0]
		name = " ".join(params[1:])
		id = client.get_id(name)
		if not id:
			return 'Penguin "{}" not found'.format(name)
		client.mail(id, postcard)

def coins(client, amount=None):
	if amount is None:
		return "Current coins: {}".format(client.coins)
	else:
		client.add_coins(amount)

def buddy(client, *params):
	name = " ".join(params)
	id = client.get_id(name)
	if not id:
		return 'Penguin "{}" not found'.format(name)
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
		name = " ".join(params)
		id = client.get_id(name)
		if not id:
			return 'Penguin "{}" not found'.format(name)
		if offset:
			client.follow(id, dx, dy)
		else:
			client.follow(id)
		return None
	if client._follow:
		return 'Currently following "{}"'.format(client.penguins[client._follow[0]].name)
	return "Currently not following"

def logout(client):
	client.logout()
	sys.exit(0)

def main():
	try:
		client = login()
	except LoginError as e:
		print e.message
		sys.exit(1)
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
	while client.connected:
		try:
			command = get_input(">>> ", commands.keys()).split(" ")
		except KeyboardInterrupt:
			print
			continue
		except EOFError:
			logout(client)
			break
		command, params = command[0], command[1:]
		if command in commands:
			function = commands[command]
			try:
				if hasattr(function, "__self__"):
					function(*params)
				else:
					message = function(client, *params)
					if message is not None:
						print message
			except TypeError as e:
				if function.__name__ + "() takes" not in e.message:
					raise
				print 'command "{}" does not take {} arguments'.format(command, len(params))
			except ClientError as e:
				pass
		elif command:
			print 'command "{}" does not exist'.format(command)

if __name__ == "__main__":
	main()
