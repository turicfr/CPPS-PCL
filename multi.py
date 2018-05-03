import sys
import logging
import common
from client import ClientError
from functools import wraps
from multiprocessing.pool import ThreadPool
from threading import Semaphore
from collections import Counter

def get_shape(shapes, shape=None):
	if shape is None:
		shape = common.get_input("Shape: ", shapes.keys())
	shape = shape.lower()
	if shape not in shapes:
		raise common.LoginError("Shape not found")
	return shapes[shape]

def for_all(clients_offsets):
	def decorator(function):
		def star(args):
			try:
				function(*args)
			except ClientError as e:
				return e
			return None
		@wraps(function)
		def wrapper(*params):
			pool = ThreadPool()
			for e in pool.imap(star, ((client, dx, dy) + params for client, dx, dy in clients_offsets)):
				if e is not None:
					print "{}: {}".format(e.client.name, e.message)
		return wrapper
	return decorator

def set_all(clients_offsets, attribute, value):
	@for_all(clients_offsets)
	def inner_set_all(client, dx, dy):
		setattr(client, attribute, value)
	inner_set_all()

def call_all(clients_offsets, method):
	@for_all(clients_offsets)
	def inner_call_all(client, dx, dy, *params):
		method(client)(*params)
	inner_call_all.__name__ = method(clients_offsets[0][0]).__name__
	inner_call_all.__self__ = clients_offsets
	return inner_call_all

def connect_client(client, user, password):
	try:
		client.connect(user, password, True)
	except ClientError as e:
		return user, e
	return user, None

def auto_login(cpps, penguins, clients):
	def callback(args):
		user, e = args
		if e is None:
			count["value"] -= 1
			print "Connected with {}! ({} left)".format(user, count["value"])
			if not count["value"]:
				semaphore.release()
		else:
			not_connected.append(e.client)
			print "{}: {}".format(user, e.message)
			if e.code == 101 or e.code == 603:
				common.remove_penguin(cpps, user, penguins)
			semaphore.release()
	count = {"value": len(clients)}
	not_connected = clients[:]
	pool = ThreadPool()
	semaphore = Semaphore(count["value"])
	for user, password in penguins[cpps].items():
		semaphore.acquire()
		if not count["value"]:
			break
		client = not_connected.pop()
		print "Connecting with {}...".format(user)
		pool.apply_async(connect_client, (client, user, password), callback=callback)
	pool.close()
	pool.join()
	assert count["value"] == len(not_connected)
	return not_connected

def manual_login(cpps, server, clients, remember):
	count = len(clients)
	for client in clients:
		while not client.connected:
			cpps, server, user, password, encrypted, client = common.get_penguin(cpps, server, remember=remember, client=client)
			print "Connecting..."
			try:
				client.connect(user, password)
			except ClientError as e:
				print e.message
				if e.code == 101 or e.code == 603:
					common.remove_penguin(cpps, user)
				continue
			count -= 1
			print "Connected! ({} left)".format(count)

def connect_clients(cpps, server, clients_offsets, remember):
	count = len(clients_offsets)
	print "Logging in with {} penguin{}...".format(count, "s" if count > 1 else "")
	clients = [client for client, dx, dy in clients_offsets]
	penguins = common.get_json("penguins")
	if cpps in penguins:
		clients_offsets = auto_login(cpps, penguins, clients)
	try:
		manual_login(cpps, server, clients, remember)
	except common.LoginError:
		logout(clients_offsets)
		raise
	print "All connected!"

def unify_clients(clients_offsets, shape):
	def unify_item(item_name):
		if item_name in shape:
			set_all(clients_offsets, item_name, shape[item_name])
	pool = ThreadPool()
	pool.map(unify_item, ["color", "head", "face", "neck", "body", "hand", "feet", "pin", "background"])

def get_penguins(cpps=None, server=None, shape=None):
	servers = common.get_json("servers")
	shapes = common.get_json("shapes")
	try:
		cpps = common.get_cpps(servers, cpps)
		server = common.get_server(servers, cpps, server)
		shape = get_shape(shapes, shape)
	except (KeyboardInterrupt, EOFError):
		raise common.LoginError()
	logger = logging.getLogger()
	logger.addHandler(logging.NullHandler())
	clients_offsets = [(common.get_client(servers, cpps, server, logger), int(offset["x"]), int(offset["y"])) for offset in shape["offsets"]]
	return cpps, server, shape, clients_offsets

def login():
	remember = common.get_remember()
	argc = len(sys.argv)
	cpps = sys.argv[1] if argc > 1 else None
	server = sys.argv[2] if argc > 2 else None
	shape = sys.argv[3] if argc > 3 else None
	cpps, server, shape, clients_offsets = get_penguins(cpps, server, shape)
	connect_clients(cpps, server, clients_offsets, remember)
	unify_clients(clients_offsets, shape)
	return clients_offsets

def show_help(clients_offsets):
	return """HELP"""

def get_id(clients_offsets, penguin_name):
	client, dx, dy = clients_offsets[0]
	return 'Penguin ID of "{}": {}'.format(penguin_name, client.get_penguin_id(penguin_name))

def name(clients_offsets, penguin_id=None):
	if penguin_id is None:
		return "\n".join(client.name for client, dx, dy in clients_offsets)
	client, dx, dy = clients_offsets[0]
	return 'Name of penguin ID {}: "{}"'.format(penguin_id, client.get_penguin(penguin_id).name)

def room(clients_offsets, room_id_or_name=None):
	if room_id_or_name is None:
		return "\n".join("{}: Current room: {}".format(client.name, client.get_room_name(client.room)) for client, dx, dy in clients_offsets)
	@for_all(clients_offsets)
	def inner_room(client, dx, dy):
		client.room = client.get_room_id(room_id_or_name)
	inner_room()

def igloo(clients_offsets, penguin_id_or_name):
	@for_all(clients_offsets)
	def inner_igloo(client, dx, dy):
		client.igloo = client.get_penguin_id(penguin_id_or_name)
	inner_igloo()

def color(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current color item ID: {}".format(client.name, client.color) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "color", item_id)

def head(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current head item ID: {}".format(client.name, client.head) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "head", item_id)

def face(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current face item ID: {}".format(client.name, client.face) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "face", item_id)

def neck(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current neck item ID: {}".format(client.name, client.neck) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "neck", item_id)

def body(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current body item ID: {}".format(client.name, client.body) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "body", item_id)

def hand(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current hand item ID: {}".format(client.name, client.hand) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "hand", item_id)

def feet(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current feet item ID: {}".format(client.name, client.feet) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "feet", item_id)

def pin(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current pin item ID: {}".format(client.name, client.pin) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "pin", item_id)

def background(clients_offsets, item_id=None):
	if item_id is None:
		return "\n".join("{}: Current background item ID: {}".format(client.name, client.background) for client, dx, dy in clients_offsets)
	set_all(clients_offsets, "background", item_id)

def inventory(clients_offsets):
	return "Current inventory:\n" + "\n".join("{} (x{})".format(item_id, count) for item_id, count in Counter(item_id for client, dx, dy in clients_offsets for item_id in client.inventory).iteritems())

def walk(clients_offsets, x, y):
	try:
		x = int(x)
		y = int(y)
	except ValueError:
		raise common.LoginError("Invalid parameters")
	@for_all(clients_offsets)
	def inner_walk(client, dx, dy):
		client.walk(x + dx, y + dy)
	inner_walk()

def say(clients_offsets, *message):
	message = " ".join(message)
	@for_all(clients_offsets)
	def inner_say(client, dx, dy):
		client.say(message)
	inner_say()

def coins(clients_offsets, amount=None):
	if amount is None:
		return "\n".join("{}: Current coins: {}".format(client.name, client.coins) for client, dx, dy in clients_offsets)
	call_all(clients_offsets, lambda c: c.add_coins)(amount)

def buddy(clients_offsets):
	@for_all(clients_offsets)
	def inner_buddy(client, dx, dy):
		client.buddy(client.get_penguin_id(penguin_id_or_name))
	inner_buddy()

def find(clients_offsets, penguin_id_or_name):
	client, dx, dy = clients_offsets[0]
	room_name = client.get_room_name(client.find_buddy(client.get_penguin_id(penguin_id_or_name)))
	return '"{}" is in {}'.format(penguin_id_or_name, room_name)

def follow(clients_offsets, penguin_id_or_name):
	@for_all(clients_offsets)
	def inner_follow(client, dx, dy):
		penguin_id = client.get_penguin_id(penguin_id_or_name)
		client.follow(penguin_id, dx, dy)
	inner_follow()

def logout(clients_offsets):
	@for_all(clients_offsets)
	def inner_logout(client, dx, dy):
		client.logout()
	inner_logout()
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
		"walk": walk,
		"dance": call_all(clients_offsets, lambda c: c.dance),
		"wave": call_all(clients_offsets, lambda c: c.wave),
		"sit": call_all(clients_offsets, lambda c: c.sit),
		"snowball": call_all(clients_offsets, lambda c: c.snowball),
		"say": say,
		"joke": call_all(clients_offsets, lambda c: c.joke),
		"emote": call_all(clients_offsets, lambda c: c.emote),
		"buy": call_all(clients_offsets, lambda c: c.add_item),
		"ai": call_all(clients_offsets, lambda c: c.add_item),
		"coins": coins,
		"ac": call_all(clients_offsets, lambda c: c.add_coins),
		"stamp": call_all(clients_offsets, lambda c: c.add_stamp),
		"add_igloo": call_all(clients_offsets, lambda c: c.add_igloo),
		"add_furniture": call_all(clients_offsets, lambda c: c.add_furniture),
		"music": call_all(clients_offsets, lambda c: c.igloo_music),
		"buddy": buddy,
		"find": find,
		"follow": follow,
		"unfollow": call_all(clients_offsets, lambda c: c.unfollow),
		"logout": logout,
		"exit": logout,
		"quit": logout
	}
	while all(client.connected for client, dx, dy in clients_offsets):
		try:
			function, command, params = common.read_command(commands)
		except EOFError:
			logout(clients_offsets)
			break
		try:
			common.execute_command(clients_offsets, function, command, params)
		except common.LoginError as e:
			print e.message

if __name__ == "__main__":
	main()
