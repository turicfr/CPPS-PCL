import sys
import logging
import common
from client import ClientError

def login():
	remember = common.get_remember()
	argc = len(sys.argv)
	cpps = sys.argv[1] if argc > 1 else None
	server = sys.argv[2] if argc > 2 else None
	user = sys.argv[3] if argc > 3 else None
	cpps, server, user, password, encrypted, client = common.get_penguin(cpps, server, user, remember)

	try:
		client.connect(user, password, encrypted)
	except ClientError as e:
		if e.code == 101 or e.code == 603:
			common.remove_penguin(cpps, user)
		raise common.LoginError("Failed to connect")
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
	return "Current internal room ID: {}".format(client.internal_room_id)

def get_id(client, penguin_name=None):
	if penguin_name is None:
		penguin_id = client.id
	else:
		penguin_id = client.get_id(penguin_name)
		if not penguin_id:
			return 'Penguin "{}" not found'.format(penguin_name)
	return "ID: {}".format(penguin_id)

def get_name(client, penguin_id=None):
	if penguin_id is None:
		penguin_name = client.name
	elif penguin_id in client.penguins:
		penguin_name = client.penguins[penguin_id].name
	else:
		return "Penguin #{} not found".format(penguin_id)
	return "Name: {}".format(penguin_name)

def room(client, room_id=None):
	if room_id is None:
		return "Current room: {}".format(client.get_room_name(client.room))
	try:
		room_id = int(room_id)
	except ValueError:
		room_name = room_id
		room_id = client.get_room_id(room_name)
		if not room_id:
			return 'Room "{}" not found'.format(room_name)
	client.room = room_id

def igloo(client, penguin_id=None):
	if penguin_id is None:
		penguin_id = client.id
	else:
		try:
			penguin_id = int(penguin_id)
		except ValueError:
			penguin_name = penguin_id
			penguin_id = client.get_id(penguin_name)
			if not penguin_id:
				return 'Penguin "{}" not found'.format(penguin_name)
	client.igloo = penguin_id

def penguins(client):
	return "\n".join(penguin.name for penguin_id, penguin in client.penguins.iteritems())

def color(client, item_id=None):
	if item_id is None:
		return "Current color: {}".format(client.color)
	else:
		client.color = item_id

def head(client, item_id=None):
	if item_id is None:
		return "Current head item: {}".format(client.head)
	else:
		client.head = item_id

def face(client, item_id=None):
	if item_id is None:
		return "Current face item: {}".format(client.face)
	else:
		client.face = item_id

def neck(client, item_id=None):
	if item_id is None:
		return "Current neck item: {}".format(client.neck)
	else:
		client.neck = item_id

def body(client, item_id=None):
	if item_id is None:
		return "Current body item: {}".format(client.body)
	else:
		client.body = item_id

def hand(client, item_id=None):
	if item_id is None:
		return "Current hand item: {}".format(client.hand)
	else:
		client.hand = item_id

def feet(client, item_id=None):
	if item_id is None:
		return "Current feet item: {}".format(client.feet)
	else:
		client.feet = item_id

def pin(client, item_id=None):
	if item_id is None:
		return "Current pin: {}".format(client.pin)
	else:
		client.pin = item_id

def background(client, item_id=None):
	if item_id is None:
		return "Current background: {}".format(client.background)
	else:
		client.background = item_id

def inventory(client):
	return "\n".join(str(item_id) for item_id in client.inventory)

def stamps(client):
	return "\n".join(client.stamps)

def say(client, *params):
	client.say(" ".join(params))

def mail(client, penguin_id, postcard_id):
	try:
		penguin_id = int(penguin_id)
	except ValueError:
		penguin_name = penguin_id
		penguin_id = client.get_id(penguin_name)
		if not penguin_id:
			return 'Penguin "{}" not found'.format(penguin_name)
	client.mail(penguin_id, postcard_id)

def coins(client, amount=None):
	if amount is None:
		return "Current coins: {}".format(client.coins)
	else:
		client.add_coins(amount)

def buddy(client, penguin_id):
	try:
		penguin_id = int(penguin_id)
	except ValueError:
		penguin_name = penguin_id
		penguin_id = client.get_id(penguin_name)
		if not penguin_id:
			return 'Penguin "{}" not found'.format(penguin_name)
	client.buddy(penguin_id)

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
		penguin_name = " ".join(params)
		penguin_id = client.get_id(penguin_name)
		if not penguin_id:
			return 'Penguin "{}" not found'.format(penguin_name)
		if offset:
			client.follow(penguin_id, dx, dy)
		else:
			client.follow(penguin_id)
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
	except common.LoginError as e:
		print e.message
		sys.exit(1)
	commands = {
		"help": help,
		"log": log,
		"internal": internal,
		"id": get_id,
		"name": get_name,
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
			command = common.get_input(">>> ", commands.keys()).split(" ")
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
			except ClientError:
				pass
		elif command:
			print 'command "{}" does not exist'.format(command)

if __name__ == "__main__":
	main()
