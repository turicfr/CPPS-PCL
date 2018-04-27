import sys
import logging
import common
from client import ClientError

offsets = []

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
			if count == 0:
				break
			print "Connected! ({} left)".format(count)

	i = 0
	while i < count:
		cpps, server, user, password, encrypted, clients[i] = common.get_penguin(cpps, server, remember=remember)
		print "Connecting..."
		try:
			clients[i].connect(user, password)
		except ClientError as e:
			print e.message
			if e.code == 101 or e.code == 603:
				common.remove_penguin(cpps, user)
			continue
		i += 1
		if i < count:
			print "Connected! ({} left)".format(count - i)
	print "All connected!"

def unify_clients(clients, shape):
	for client in clients:
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
	except KeyboardInterrupt:
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
	global offsets
	cpps, server, shape, offsets, clients = get_penguins(cpps, server, shape)

	connect_clients(cpps, server, clients, remember)
	unify_clients(clients, shape)
	return clients

def help(clients):
	return """HELP"""

def room(clients, room_id):
	try:
		room_id = int(room_id)
	except ValueError:
		room_name = room_id
		room_id = clients[0].get_room_id(room_name)
		if not room_id:
			return 'Room "{}" not found'.format(room_name)
	for client in clients:
		try:
			client.room = room_id
		except ClientError:
			pass

def igloo(clients, penguin_id):
	try:
		penguin_id = int(penguin_id)
	except ValueError:
		penguin_name = penguin_id
		penguin_id = clients[0].get_id(penguin_name)
		if not penguin_id:
			return 'Penguin "{}" not found'.format(penguin_name)
	for client in clients:
		try:
			client.igloo = penguin_id
		except ClientError:
			pass

def color(clients, item_id):
	for client in clients:
		try:
			client.color = item_id
		except ClientError:
			pass

def head(clients, item_id):
	for client in clients:
		try:
			client.head = item_id
		except ClientError:
			pass

def face(clients, item_id):
	for client in clients:
		try:
			client.face = item_id
		except ClientError:
			pass

def neck(clients, item_id):
	for client in clients:
		try:
			client.neck = item_id
		except ClientError:
			pass

def body(clients, item_id):
	for client in clients:
		try:
			client.body = item_id
		except ClientError:
			pass

def hand(clients, item_id):
	for client in clients:
		try:
			client.hand = item_id
		except ClientError:
			pass

def feet(clients, item_id):
	for client in clients:
		try:
			client.feet = item_id
		except ClientError:
			pass

def pin(clients, item_id):
	for client in clients:
		try:
			client.pin = item_id
		except ClientError:
			pass

def background(clients, item_id):
	for client in clients:
		try:
			client.background = item_id
		except ClientError:
			pass

# TODO: input validation
def walk(clients, x, y):
	for client, (dx, dy) in zip(clients, offsets):
		try:
			client.walk(int(x) + dx, int(y) + dy)
		except ClientError:
			pass

def dance(clients):
	for client in clients:
		try:
			client.dance()
		except ClientError:
			pass

def wave(clients):
	for client in clients:
		try:
			client.wave()
		except ClientError:
			pass

def sit(clients, direction=None):
	for client in clients:
		try:
			if direction is None:
				client.sit()
			else:
				client.sit(direction)
		except ClientError:
			pass

def snowball(clients, x, y):
	for client in clients:
		try:
			client.snowball(x, y)
		except ClientError:
			pass

def say(clients, *params):
	message = " ".join(params)
	for client in clients:
		try:
			client.say(message)
		except ClientError:
			pass

def joke(clients, joke_id):
	for client in clients:
		try:
			client.joke(joke_id)
		except ClientError:
			pass

def emote(clients, emote):
	for client in clients:
		try:
			client.emote(emote)
		except ClientError:
			pass

def add_item(clients, item_id):
	for client in clients:
		try:
			client.add_item(item_id)
		except ClientError:
			pass

def coins(clients, amount):
	for client in clients:
		try:
			client.add_item(amount)
		except ClientError:
			pass

def follow(clients, *params):
	penguin_name = " ".join(params)
	penguin_id = clients[0].get_id(penguin_name)
	if not penguin_id:
		return 'Penguin "{}" not found'.format(penguin_name)
	for client, (dx, dy) in zip(clients, offsets):
		try:
			client.follow(penguin_id, dx, dy)
		except ClientError:
			pass

def unfollow(clients):
	for client in clients:
		try:
			client.unfollow()
		except ClientError:
			pass

def logout(clients):
	for client in clients:
		try:
			client.logout()
		except ClientError:
			pass
	sys.exit(0)

def main():
	try:
		clients = login()
	except common.LoginError as e:
		print e.message
		sys.exit(1)
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
	while all(client.connected for client in clients):
		try:
			command = common.get_input(">>> ", commands.keys()).split(" ")
		except KeyboardInterrupt:
			print
			continue
		except EOFError:
			logout(clients)
			break
		command, params = command[0], command[1:]
		if command in commands:
			function = commands[command]
			try:
				message = function(clients, *params)
				if message is not None:
					print message
			except TypeError as e:
				if function.__name__ + "() takes" not in e.message:
					raise
				print 'command "{}" does not take {} arguments'.format(command, len(params))
			except ClientError:
				pass
		elif command:
			print 'command "{}" does not exist'.format(command)

if __name__ == "__main__":
	main()
