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

def show_help(client):
	return """HELP"""

def log(client, level_name=None):
	if level_name is None:
		level_name = "all" if client.logger.level else "error"
	level = {
		"all": logging.NOTSET,
		"debug": logging.DEBUG,
		"info": logging.INFO,
		"warning": logging.WARNING,
		"error": logging.ERROR,
		"critical": logging.CRITICAL
	}.get(level_name)
	if level is None:
		raise ClientError('Unknown logging level "{}"'.format(level_name))
	client.logger.setLevel(level)
	return "Logging {} messages".format(level_name)

def internal(client):
	return "Current internal room ID: {}".format(client.internal_room_id)

def get_id(client, penguin_name=None):
	if penguin_name is None:
		return "Current penguin ID: {}".format(client.id)
	return 'Penguin ID of "{}": {}'.format(penguin_name, client.get_penguin_id(penguin_name))

def name(client, penguin_id=None):
	if penguin_id is None:
		return "Current penguin name: {}".format(client.name)
	return 'Name of penguin ID {}: "{}"'.format(penguin_id, client.get_penguin(penguin_id).name)

def room(client, room_id_or_name=None):
	if room_id_or_name is None:
		return "Current room: {}".format(client.get_room_name(client.room))
	client.room = client.get_room_id(room_id_or_name)

def igloo(client, penguin_id_or_name=None):
	client.igloo = client.id if penguin_id_or_name is None else client.get_penguin_id(penguin_id_or_name)

def penguins(client):
	return "\n".join("{} (ID: {})".format(penguin.name, penguin.id) for penguin in client.penguins.itervalues())

def color(client, item_id=None):
	if item_id is None:
		return "Current color item ID: {}".format(client.color)
	client.color = item_id

def head(client, item_id=None):
	if item_id is None:
		return "Current head item ID: {}".format(client.head)
	client.head = item_id

def face(client, item_id=None):
	if item_id is None:
		return "Current face item ID: {}".format(client.face)
	client.face = item_id

def neck(client, item_id=None):
	if item_id is None:
		return "Current neck item ID: {}".format(client.neck)
	client.neck = item_id

def body(client, item_id=None):
	if item_id is None:
		return "Current body item ID: {}".format(client.body)
	client.body = item_id

def hand(client, item_id=None):
	if item_id is None:
		return "Current hand item ID: {}".format(client.hand)
	client.hand = item_id

def feet(client, item_id=None):
	if item_id is None:
		return "Current feet item ID: {}".format(client.feet)
	client.feet = item_id

def pin(client, item_id=None):
	if item_id is None:
		return "Current pin item ID: {}".format(client.pin)
	client.pin = item_id

def background(client, item_id=None):
	if item_id is None:
		return "Current background item ID: {}".format(client.background)
	client.background = item_id

def inventory(client):
	return "\n".join(str(item_id) for item_id in client.inventory)

def stamps(client):
	return "\n".join(str(stamp_id) for stamp_id in client.stamps)

def say(client, *message):
	client.say(" ".join(message))

def mail(client, penguin_id_or_name, postcard_id):
	client.mail(client.get_penguin_id(penguin_id_or_name), postcard_id)

def coins(client, amount=None):
	if amount is None:
		return "Current coins: {}".format(client.coins)
	client.add_coins(amount)

def buddy(client, penguin_id_or_name):
	client.buddy(client.get_penguin_id(penguin_id_or_name))

def find(client, penguin_id_or_name):
	room_name = client.get_room_name(client.find_buddy(client.get_penguin_id(penguin_id_or_name)))
	return '"{}" is in {}'.format(penguin_id_or_name, room_name)

def follow(client, penguin_id_or_name=None, dx=None, dy=None):
	if penguin_id_or_name is None:
		if client._follow:
			return 'Currently following "{}"'.format(client.get_penguin_name(client._follow[0]))
		return "Currently not following"
	penguin_id = client.get_penguin_id(penguin_id_or_name)
	if dx is None:
		client.follow(penguin_id)
	elif dy is None:
		raise ClientError("Invalid parameters")
	else:
		try:
			dx = int(dx)
			dy = int(dy)
		except ValueError:
			raise ClientError("Invalid parameters")
		client.follow(penguin_id, dx, dy)

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
		"help": show_help,
		"log": log,
		"internal": internal,
		"id": get_id,
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
		"find": find,
		"follow": follow,
		"unfollow": client.unfollow,
		"logout": logout,
		"exit": logout,
		"quit": logout
	}
	while client.connected:
		try:
			function, command, params = common.read_command(commands)
		except EOFError:
			logout(client)
			break
		try:
			common.execute_command(client, function, command, params)
		except ClientError:
			pass

if __name__ == "__main__":
	main()
