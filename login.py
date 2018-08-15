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

def log(client, level=None):
	if level is None:
		if client.logger.level:
			level = logging.NOTSET
			level_name = "all"
		else:
			level = logging.ERROR
			level_name = "error"
	else:
		level, level_name = level
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
		client.follow(penguin_id, dx, dy)

def logout(client):
	client.logout()
	sys.exit(0)

def main():
	try:
		client = login()
	except common.LoginError as e:
		print e
		sys.exit(1)
	commands = common.Command.index(
		common.Command("log", log, common.Parameter.logging_level(required=False, help="Logging level"), help="Set logging level"),
		common.Command("internal", internal, help="Get current internal room ID"),
		common.Command("id", get_id, common.Parameter.penguin_name(required=False, help="Penguin name"), varargs=common.VarArgs.SINGLE_THREADED, help="Get penguin ID"),
		common.Command("name", name, common.Parameter.int_param("penguin_id", required=False, help="Penguin ID"), varargs=common.VarArgs.SINGLE_THREADED, help="Get penguin name"),
		common.Command("room", room, common.Parameter("room_name", common.get_json("rooms").values(), required=False, help="Room name"), help="Go to room"),
		common.Command("igloo", igloo, common.Parameter.penguin_name(required=False, help="Penguin name"), help="Go to igloo"),
		common.Command("penguins", penguins, help="Get all penguins in current room"),
		common.Command("color", color, common.Parameter.int_param("item_id", required=False, help="Color item ID"), help="Get current color item ID / Equip color item"),
		common.Command("head", head, common.Parameter.int_param("item_id", required=False, help="Head item ID"), help="Get current head item ID / Equip head item"),
		common.Command("face", face, common.Parameter.int_param("item_id", required=False, help="Face item ID"), help="Get current face item ID / Equip face item"),
		common.Command("neck", neck, common.Parameter.int_param("item_id", required=False, help="Neck item ID"), help="Get current neck item ID / Equip neck item"),
		common.Command("body", body, common.Parameter.int_param("item_id", required=False, help="Body item ID"), help="Get current body item ID / Equip body item"),
		common.Command("hand", hand, common.Parameter.int_param("item_id", required=False, help="Hand item ID"), help="Get current hand item ID / Equip hand item"),
		common.Command("feet", feet, common.Parameter.int_param("item_id", required=False, help="Feet item ID"), help="Get current feet item ID / Equip feet item"),
		common.Command("pin", pin, common.Parameter.int_param("item_id", required=False, help="Pin item ID"), help="Get current pin item ID / Equip pin item"),
		common.Command("background", background, common.Parameter.int_param("item_id", required=False, help="Background item ID"), help="Get current background item ID / Equip background item"),
		common.Command("clothes", clothes, common.Parameter.penguin_name(required=False, help="Penguin name"), varargs=common.VarArgs.SINGLE_THREADED, help="Get all currently equipped item IDs"),
		common.Command("inventory", inventory, help="Get current inventory"),
		common.Command("buddies", buddies, help="Get all current buddies"),
		common.Command("stamps", stamps, common.Parameter.penguin_name(required=False, help="Penguin name"), help="Get all currently earned stamps"),
		common.Command("walk", Client.walk, common.Parameter.int_param("x", help="X"), common.Parameter.int_param("y", help="Y"), help="Walk"),
		common.Command("dance", Client.dance, help="Dance"),
		common.Command("wave", Client.wave, help="Wave"),
		common.Command("sit", Client.sit, common.Parameter("direction", ["s", "e", "w", "nw", "sw", "ne", "se", "n"], required=False, help="Direction"), help="Sit"),
		common.Command("snowball", Client.snowball, common.Parameter.int_param("x", help="X"), common.Parameter.int_param("y", help="Y"), help="Throw snowball"),
		common.Command("say", say, varargs=common.VarArgs.NORMAL, help="Say message"),
		common.Command("joke", Client.joke, common.Parameter.int_param("joke_id", help="Joke ID"), help="Tell a joke"),
		common.Command("emote", Client.emote, common.Parameter.int_param("emote_id", help="Emote ID"), help="React an emote"),
		common.Command("mail", mail, common.Parameter.other_penguin_name(help="Penguin name"), common.Parameter.int_param("postcard_id", help="Postcard ID"), help="Send a postcard"),
		common.Command("buy", Client.add_item, common.Parameter.int_param("item_id", help="Item ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy item"),
		common.Command("ai", Client.add_item, common.Parameter.int_param("item_id", help="Item ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy item"),
		common.Command("coins", coins, common.Parameter.int_param("amount", required=False, help="Amount"), help="Get current coins / Earn coins"),
		common.Command("ac", Client.add_coins, common.Parameter.int_param("amount", help="Amount"), help="Earn coins"),
		common.Command("stamp", Client.add_stamp, common.Parameter.int_param("stamp_id", help="Stamp ID"), varargs=common.VarArgs.MULTI_THREADED, help="Earn stamp"),
		common.Command("add_igloo", Client.add_igloo, common.Parameter.int_param("igloo_id", help="Igloo ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy igloo"),
		common.Command("add_furniture", Client.add_furniture, common.Parameter.int_param("furniture_id", help="Furniture ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy furniture"),
		common.Command("music", Client.igloo_music, common.Parameter.int_param("music_id", help="Music ID"), help="Set current igloo music"),
		common.Command("buddy", buddy, common.Parameter.other_penguin_name(help="Penguin name"), varargs=common.VarArgs.MULTI_THREADED, help="Send buddy request"),
		common.Command("find", find, common.Parameter.other_penguin_name(help="Penguin name"), varargs=common.VarArgs.MULTI_THREADED, help="Find buddy"),
		common.Command("follow", follow, common.Parameter.other_penguin_name(help="Penguin name"), help="Follow penguin"),
		common.Command("unfollow", Client.unfollow, help="Stop following"),
		common.Command("logout", logout, help="Logout"),
		common.Command("exit", logout, help="Logout"),
		common.Command("quit", logout, help="Logout")
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
