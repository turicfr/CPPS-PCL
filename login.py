import sys
import logging
import common
from client import Client, ClientError

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
		raise common.LoginError('Unknown logging level "{}"'.format(level_name))
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
	return "Current penguins in {}:\n{}".format(client.get_room_name(client.room), "\n".join("{} (ID: {})".format(penguin.name, penguin.id) for penguin in client.penguins.itervalues()))

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

def clothes(client, penguin_id_or_name=None):
	if penguin_id_or_name is None:
		return """Current item IDs:
color: {}
head: {}
face: {}
neck: {}
body: {}
hand: {}
feet: {}
pin: {}
background: {}""".format(client.color, client.head, client.face, client.neck, client.body, client.hand, client.feet, client.pin, client.background)
	penguin = client.get_penguin(client.get_penguin_id(penguin_id_or_name))
	return """Current item IDs of "{}":
color: {}
head: {}
face: {}
neck: {}
body: {}
hand: {}
feet: {}
pin: {}
background: {}""".format(penguin.name, penguin.color, penguin.head, penguin.face, penguin.neck, penguin.body, penguin.hand, penguin.feet, penguin.pin, penguin.background)

def inventory(client):
	return "Current inventory:\n" + "\n".join(str(item_id) for item_id in client.inventory)

def buddies(client):
	buddies = client.buddies
	if not buddies:
		return "Currently has no buddies"
	return "Current buddies:\n{}".format("\n".join("{} (ID: {}, {})".format(penguin.name, penguin.id, "online" if penguin.online else "offline") for penguin in buddies.itervalues()))

def stamps(client, penguin_id_or_name=None):
	if penguin_id_or_name is None:
		penguin_id = client.id
		stamps = client.stamps
	else:
		penguin_id = client.get_penguin_id(penguin_id_or_name)
		stamps = client.get_stamps(penguin_id)
	penguin = client.get_penguin(penguin_id)
	if not stamps:
		return '"{}" has no stamps'.format(penguin.name)
	return 'Stamps of "{}":\n'.format(penguin.name) + "\n".join(str(stamp_id) for stamp_id in stamps)

def say(client, *message):
	client.say(" ".join(message))

def mail(client, penguin_id_or_name, postcard_id):
	client.mail(client.get_penguin_id(penguin_id_or_name), postcard_id)

def coins(client, amount=None):
	if amount is None:
		return "Current coins: {}".format(client.coins)
	client.add_coins(amount)

def buddy(client, penguin_id_or_name):
	client.add_buddy(client.get_penguin_id(penguin_id_or_name))

def find(client, penguin_id_or_name):
	penguin = client.get_penguin(client.get_penguin_id(penguin_id_or_name))
	return '"{}" is in {}'.format(penguin.name, client.get_room_name(client.find_buddy(penguin.id)))

def follow(client, penguin_id_or_name=None, dx=None, dy=None):
	if penguin_id_or_name is None:
		if client._follow:
			return 'Currently following "{}"'.format(client.get_penguin(client._follow[0]).name)
		return "Currently not following"
	penguin_id = client.get_penguin_id(penguin_id_or_name)
	if dx is None:
		client.follow(penguin_id)
	elif dy is None:
		raise common.LoginError("Invalid parameters")
	else:
		try:
			dx = int(dx)
			dy = int(dy)
		except ValueError:
			common.LoginError("Invalid parameters")
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
	int_param = lambda name, required=True: common.Parameter(name, [], required=required, type=int)
	penguin_name_param = lambda required=True: common.Parameter("penguin_name", lambda c: [penguin.name for penguin in c.penguins.itervalues()], required=required)
	other_penguin_name_param = lambda required=True: common.Parameter("penguin_name", lambda c: [penguin.name for penguin in c.penguins.itervalues() if penguin.id != client.id], required=required)
	commands = common.Command.index(
		common.Command("help", show_help),
		common.Command("log", log, common.Parameter("level", ["all", "debug", "info", "warning", "error", "critical"], required=False)),
		common.Command("internal", internal),
		common.Command("id", get_id, penguin_name_param(required=False)),
		common.Command("name", name, int_param("penguin_id", required=False)),
		common.Command("room", room, common.Parameter("room_name", common.get_json("rooms").values(), required=False)),
		common.Command("igloo", igloo, penguin_name_param(required=False)),
		common.Command("penguins", penguins),
		common.Command("color", color, int_param("item_id", required=False)),
		common.Command("head", head, int_param("item_id", required=False)),
		common.Command("face", face, int_param("item_id", required=False)),
		common.Command("neck", neck, int_param("item_id", required=False)),
		common.Command("body", body, int_param("item_id", required=False)),
		common.Command("hand", hand, int_param("item_id", required=False)),
		common.Command("feet", feet, int_param("item_id", required=False)),
		common.Command("pin", pin, int_param("item_id", required=False)),
		common.Command("background", background, int_param("item_id", required=False)),
		common.Command("clothes", clothes, penguin_name_param(required=False)),
		common.Command("inventory", inventory),
		common.Command("buddies", buddies),
		common.Command("stamps", stamps, penguin_name_param(required=False)),
		common.Command("walk", Client.walk, int_param("x"), int_param("y")),
		common.Command("dance", Client.dance),
		common.Command("wave", Client.wave),
		common.Command("sit", Client.sit, common.Parameter("direction", ["s", "e", "w", "nw", "sw", "ne", "se", "n"])),
		common.Command("snowball", Client.snowball, int_param("x"), int_param("y")),
		common.Command("say", say, varargs=True),
		common.Command("joke", Client.joke, int_param("joke_id")),
		common.Command("emote", Client.emote, int_param("emote_id")),
		common.Command("mail", mail, other_penguin_name_param(), int_param("postcard_id")),
		common.Command("buy", Client.add_item, int_param("item_id")),
		common.Command("ai", Client.add_item, int_param("item_id")),
		common.Command("coins", coins, int_param("amount", required=False)),
		common.Command("ac", Client.add_coins, int_param("amount")),
		common.Command("stamp", Client.add_stamp, int_param("stamp_id")),
		common.Command("add_igloo", Client.add_igloo, int_param("igloo_id")),
		common.Command("add_furniture", Client.add_furniture, int_param("furniture_id")),
		common.Command("music", Client.igloo_music, int_param("music_id")),
		common.Command("buddy", buddy, other_penguin_name_param()),
		common.Command("find", find, other_penguin_name_param()),
		common.Command("follow", follow, other_penguin_name_param()),
		common.Command("unfollow", Client.unfollow),
		common.Command("logout", logout),
		common.Command("exit", logout),
		common.Command("quit", logout)
	)
	while client.connected:
		try:
			command, params = common.Command.read(client, commands)
		except EOFError:
			logout(client)
			break
		command.execute(client, params)

if __name__ == "__main__":
	main()
