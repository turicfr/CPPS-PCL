import sys
import logging
import common
from client import ClientError
from functools import wraps

def get_shape(shapes, shape=None):
	if shape is None:
		shape = common.get_input("Shape: ", shapes.keys())
	shape = shape.lower()
	if shape not in shapes:
		raise common.LoginError("Shape not found")
	return shapes[shape]

def connect_clients(cpps, server, clients, remember):
	count = len(clients)
	print "Logging in with {} penguin{}...".format(count, "s" if count > 1 else "")

	penguins = common.get_json("penguins")
	if cpps in penguins:
		# TODO: multithreading
		for user, password in penguins[cpps].items():
			print "Connecting..."
			try:
				clients[count - 1].connect(user, password, True)
			except ClientError as e:
				print "{}: {}".format(user, e.message)
				if e.code == 101 or e.code == 603:
					common.remove_penguin(cpps, user, penguins)
				continue
			count -= 1
			if not count:
				break
			print "Connected! ({} left)".format(count)

	while count:
		cpps, server, user, password, encrypted, clients[count - 1] = common.get_penguin(cpps, server, remember=remember)
		print "Connecting..."
		try:
			clients[count - 1].connect(user, password)
		except ClientError as e:
			print e.message
			if e.code == 101 or e.code == 603:
				common.remove_penguin(cpps, user)
			continue
		count -= 1
		if count:
			print "Connected! ({} left)".format(count)
	print "All connected!"

# TODO: multithreading
def for_all(function):
	@wraps(function)
	def inner_for_all(clients_offsets, *params):
		for client, (dx, dy) in clients_offsets:
			function(client, dx, dy, *params)
	return inner_for_all

def set_all(attribute):
	@for_all
	def inner_set_all(client, dx, dy, *params):
		setattr(client, attribute, *params)
	return inner_set_all

def call_all(method):
	@for_all
	def inner_call_all(client, dx, dy, *params):
		method(client)(*params)
	return inner_call_all

# TODO: multithreading
@for_all
def unify_clients(client, dx, dy, shape):
	if "color" in shape:
		try:
			client.color = shape["color"]
		except ClientError as e:
			print e.message
	if "head" in shape:
		try:
			client.head = shape["head"]
		except ClientError as e:
			print e.message
	if "face" in shape:
		try:
			client.face = shape["face"]
		except ClientError as e:
			print e.message
	if "neck" in shape:
		try:
			client.neck = shape["neck"]
		except ClientError as e:
			print e.message
	if "body" in shape:
		try:
			client.body = shape["body"]
		except ClientError as e:
			print e.message
	if "hand" in shape:
		try:
			client.hand = shape["hand"]
		except ClientError as e:
			print e.message
	if "feet" in shape:
		try:
			client.feet = shape["feet"]
		except ClientError as e:
			print e.message
	if "pin" in shape:
		try:
			client.pin = shape["pin"]
		except ClientError as e:
			print e.message
	if "background" in shape:
		try:
			client.background = shape["background"]
		except ClientError as e:
			print e.message

def get_penguins(cpps=None, server=None, shape=None):
	servers = common.get_json("servers")
	shapes = common.get_json("shapes")
	try:
		cpps = common.get_cpps(servers, cpps)
		server = common.get_server(servers, cpps, server)
		shape = get_shape(shapes, shape)
	except (KeyboardInterrupt, EOFError):
		raise common.LoginError()
	offsets = [(int(offset["x"]), int(offset["y"])) for offset in shape["offsets"]]
	logger = logging.getLogger()
	logger.addHandler(logging.NullHandler())
	clients = [common.get_client(servers, cpps, server, logger) for offset in offsets]
	return cpps, server, shape, offsets, clients

def login():
	remember = common.get_remember()
	argc = len(sys.argv)
	cpps = sys.argv[1] if argc > 1 else None
	server = sys.argv[2] if argc > 2 else None
	shape = sys.argv[3] if argc > 3 else None
	cpps, server, shape, offsets, clients = get_penguins(cpps, server, shape)
	clients_offsets = zip(clients, offsets)
	connect_clients(cpps, server, clients, remember)
	unify_clients(clients_offsets, shape)
	return clients_offsets

def show_help(clients_offsets):
	return """HELP"""

def get_id(clients_offsets, penguin_name):
	client, offset = clients_offsets[0]
	return 'Penguin ID of "{}": {}'.format(penguin_name, client.get_penguin_id(penguin_name))

def name(clients_offsets, penguin_id):
	client, offset = clients_offsets[0]
	return 'Name of penguin ID {}: "{}"'.format(penguin_id, client.get_penguin(penguin_id).name)

def room(clients_offsets, room_id_or_name):
	@for_all
	def inner_room(client, dx, dy):
		client.room = client.get_room_id(room_id_or_name)
	inner_room(clients_offsets)

def igloo(clients_offsets, penguin_id_or_name):
	@for_all
	def inner_igloo(client, dx, dy):
		client.igloo = client.get_penguin_id(penguin_id_or_name)
	inner_igloo(clients_offsets)

def walk(clients_offsets, x, y):
	try:
		x = int(x)
		y = int(y)
	except ValueError:
		raise ClientError("Invalid parameters")
	@for_all
	def inner_walk(client, dx, dy):
		client.walk(x + dx, y + dy)
	inner_walk(clients_offsets)

def say(clients_offsets, *message):
	message = " ".join(message)
	@for_all
	def inner_say(client, dx, dy):
		client.say(message)
	inner_say(clients_offsets)

def buddy(clients_offsets):
	@for_all
	def inner_buddy(client, dx, dy):
		client.buddy(client.get_penguin_id(penguin_id_or_name))
	inner_buddy(clients_offsets)

def find(clients_offsets, penguin_id_or_name):
	client, offset = clients_offsets[0]
	room_name = client.get_room_name(client.find_buddy(client.get_penguin_id(penguin_id_or_name)))
	return '"{}" is in {}'.format(penguin_id_or_name, room_name)

def follow(clients_offsets, penguin_id_or_name):
	@for_all
	def inner_follow(client, dx, dy):
		penguin_id = client.get_penguin_id(penguin_id_or_name)
		client.follow(penguin_id, dx, dy)
	inner_follow(clients_offsets)

def logout(clients_offsets):
	@for_all
	def inner_logout(client, dx, dy):
		client.logout()
	inner_logout(clients_offsets)
	sys.exit()

def main():
	try:
		clients_offsets = login()
	except common.LoginError as e:
		print e.message
		sys.exit(1)
	commands = {
		"help": show_help,
		"id": get_id,
		"name": name,
		"room": room,
		"igloo": igloo,
		"color": set_all("color"),
		"head": set_all("head"),
		"face": set_all("face"),
		"neck": set_all("neck"),
		"body": set_all("body"),
		"hand": set_all("hand"),
		"feet": set_all("feet"),
		"pin": set_all("pin"),
		"background": set_all("background"),
		"walk": walk,
		"dance": call_all(lambda c: c.dance),
		"wave": call_all(lambda c: c.wave),
		"sit": call_all(lambda c: c.sit),
		"snowball": call_all(lambda c: c.snowball),
		"say": say,
		"joke": call_all(lambda c: c.joke),
		"emote": call_all(lambda c: c.emote),
		"buy": call_all(lambda c: c.add_item),
		"ai": call_all(lambda c: c.add_item),
		"coins": call_all(lambda c: c.add_coins),
		"ac": call_all(lambda c: c.add_coins),
		"stamp": call_all(lambda c: c.add_stamp),
		"add_igloo": call_all(lambda c: c.add_igloo),
		"add_furniture": call_all(lambda c: c.add_furniture),
		"music": call_all(lambda c: c.igloo_music),
		"buddy": buddy,
		"find": find,
		"follow": follow,
		"unfollow": call_all(lambda c: c.unfollow),
		"logout": logout,
		"exit": logout,
		"quit": logout
	}
	while all(client.connected for client, offset in clients_offsets):
		try:
			function, command, params = common.read_command(commands)
		except EOFError:
			logout(clients_offsets)
			break
		try:
			common.execute_command(clients_offsets, function, command, params)
		except ClientError as e:
			print e.message

if __name__ == "__main__":
	main()
