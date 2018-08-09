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

def for_all(function):
	def star(args):
		try:
			function(*args)
		except:
			return sys.exc_info()
		return None
	@wraps(function)
	def wrapper(clients_offsets, *params):
		pool = ThreadPool()
		for exc_info in pool.imap(star, ((client, dx, dy) + params for client, dx, dy in clients_offsets)):
			if exc_info is not None:
				exc_type, exc, exc_tb = exc_info
				if not isinstance(exc, ClientError):
					raise exc_type, exc, exc_tb
				print "{}: {}".format(exc.client.name, exc)
	return wrapper

def set_all(clients_offsets, attribute, value):
	@for_all
	def inner_set_all(client, dx, dy):
		setattr(client, attribute, value)
	inner_set_all(clients_offsets)

def call_all(method):
	@for_all
	def inner_call_all(client, dx, dy, *params):
		getattr(client, method)(*params)
	inner_call_all.__name__ = method
	return inner_call_all

def equip(client, shape, pool):
	def inner_equip(item_name):
		if item_name in shape:
			try:
				setattr(client, item_name, shape[item_name])
			except ClientError as e:
				print "{}: {}".format(e.client.name, e)
	pool.map_async(inner_equip, ["color", "head", "face", "neck", "body", "hand", "feet", "pin", "background"])

def connect_client(client, user, password, shape, pool):
	print "Connecting with {}...".format(user)
	try:
		client.connect(user, password, True)
	except ClientError as e:
		return user, e
	equip(client, shape, pool)
	return user, None

def auto_login(cpps, shape, penguins, clients):
	def callback(args):
		user, e = args
		if e is None:
			count[0] -= 1
			print "Connected with {}! ({} left)".format(user, count[0])
			if not count[0]:
				semaphore.release()
		else:
			not_connected.append(e.client)
			print "{}: {}".format(user, e)
			if e.code == 101 or e.code == 603:
				common.remove_penguin(cpps, user, penguins)
			semaphore.release()
	count = [len(clients)]
	not_connected = clients[:]
	pool = ThreadPool()
	results = []
	semaphore = Semaphore(count[0])
	for user, password in penguins[cpps].items():
		semaphore.acquire()
		if not count[0]:
			break
		results.append(pool.apply_async(connect_client, (not_connected.pop(), user, password, shape, pool), callback=callback))
	for result in results:
		result.wait()
	pool.close()
	pool.join()
	assert count[0] == len(not_connected)
	return not_connected

def manual_login(cpps, server, shape, connected, not_connected, remember):
	pool = ThreadPool()
	for i, client in enumerate(not_connected):
		while not client.connected:
			cpps, server, user, password, encrypted, client = common.get_penguin(cpps, server, remember=remember, client=client)
			if any(client.name.lower() == user for client in connected):
				print "Already logged in"
				continue
			print "Connecting..."
			try:
				client.connect(user, password)
			except ClientError as e:
				print e
				if e.code == 101 or e.code == 603:
					common.remove_penguin(cpps, user)
				continue
			equip(client, shape, pool)
			print "Connected! ({} left)".format(len(not_connected) - i - 1)
	pool.close()
	pool.join()

def connect_clients(cpps, server, shape, clients_offsets, remember):
	clients = [client for client, dx, dy in clients_offsets]
	print "Logging in with {} penguin{}...".format(len(clients), "s" if len(clients) > 1 else "")
	if cpps == "cpr":
		try:
			import recaptcha
		except ImportError:
			raise common.LoginError("cefpython is not installed; Please install it using the following command and try again:\npip install cefpython3")
		recaptcha.preload_tokens(len(clients))
	penguins = common.get_json("penguins")
	not_connected = auto_login(cpps, shape, penguins, clients) if cpps in penguins else clients
	connected = [client for client in clients if client not in not_connected]
	try:
		manual_login(cpps, server, shape, connected, not_connected, remember)
	except common.LoginError:
		logout(clients_offsets)
		raise
	print "All connected!"

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
	connect_clients(cpps, server, shape, clients_offsets, remember)
	return clients_offsets

def internal(clients_offsets):
	return "\n".join('Current internal room ID of "{}": {}'.format(client.name, client.internal_room_id) for client, dx, dy in clients_offsets)

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
	@for_all
	def inner_room(client, dx, dy):
		client.room = client.get_room_id(room_id_or_name)
	inner_room(clients_offsets)

def igloo(clients_offsets, penguin_id_or_name):
	@for_all
	def inner_igloo(client, dx, dy):
		client.igloo = client.get_penguin_id(penguin_id_or_name)
	inner_igloo(clients_offsets)

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

def clothes(clients_offsets, penguin_id_or_name):
	client, dx, dy = clients_offsets[0]
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

def inventory(clients_offsets):
	return "Current inventory:\n" + "\n".join("{} (x{})".format(item_id, count) for item_id, count in Counter(item_id for client, dx, dy in clients_offsets for item_id in client.inventory).iteritems())

def walk(clients_offsets, x, y):
	try:
		x = int(x)
		y = int(y)
	except ValueError:
		raise common.LoginError("Invalid parameters")
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

def coins(clients_offsets, amount=None):
	if amount is None:
		return "\n".join("{}: Current coins: {}".format(client.name, client.coins) for client, dx, dy in clients_offsets)
	call_all("add_coins")(clients_offsets, amount)

def buddy(clients_offsets, penguin_id_or_name):
	@for_all
	def inner_buddy(client, dx, dy):
		client.add_buddy(client.get_penguin_id(penguin_id_or_name))
	inner_buddy(clients_offsets)

def find(clients_offsets, penguin_id_or_name):
	client, dx, dy = clients_offsets[0]
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
		print e
		sys.exit(1)
	client, dx, dy = clients_offsets[0]
	commands = common.Command.index(
		common.Command("internal", internal, help="Get current internal room ID"),
		common.Command("id", get_id, common.Parameter.penguin_name(help="Penguin name"), varargs=common.VarArgs.SINGLE_THREADED, help="Get penguin ID"),
		common.Command("name", name, common.Parameter.int_param("penguin_id", required=False, help="Penguin ID"), varargs=common.VarArgs.SINGLE_THREADED, help="Get penguin name"),
		common.Command("room", room, common.Parameter("room_name", common.get_json("rooms").values(), help="Room name"), help="Go to room"),
		common.Command("igloo", igloo, common.Parameter.penguin_name(help="Penguin name"), help="Go to igloo"),
		common.Command("color", color, common.Parameter.int_param("item_id", required=False, help="Color item ID"), help="Get current color item ID / Equip color item"),
		common.Command("head", head, common.Parameter.int_param("item_id", required=False, help="Head item ID"), help="Get current head item ID / Equip head item"),
		common.Command("face", face, common.Parameter.int_param("item_id", required=False, help="Face item ID"), help="Get current face item ID / Equip face item"),
		common.Command("neck", neck, common.Parameter.int_param("item_id", required=False, help="Neck item ID"), help="Get current neck item ID / Equip neck item"),
		common.Command("body", body, common.Parameter.int_param("item_id", required=False, help="Body item ID"), help="Get current body item ID / Equip body item"),
		common.Command("hand", hand, common.Parameter.int_param("item_id", required=False, help="Hand item ID"), help="Get current hand item ID / Equip hand item"),
		common.Command("feet", feet, common.Parameter.int_param("item_id", required=False, help="Feet item ID"), help="Get current feet item ID / Equip feet item"),
		common.Command("pin", pin, common.Parameter.int_param("item_id", required=False, help="Pin item ID"), help="Get current pin item ID / Equip pin item"),
		common.Command("background", background, common.Parameter.int_param("item_id", required=False, help="Background item ID"), help="Get current background item ID / Equip background item"),
		common.Command("inventory", inventory, help="Get current inventory"),
		common.Command("walk", walk, common.Parameter.int_param("x", help="X"), common.Parameter.int_param("y", help="Y"), help="Walk"),
		common.Command("dance", call_all("dance"), help="Dance"),
		common.Command("wave", call_all("wave"), help="Wave"),
		common.Command("sit", call_all("sit"), common.Parameter("direction", ["s", "e", "w", "nw", "sw", "ne", "se", "n"], required=False, help="Direction"), help="Sit"),
		common.Command("snowball", call_all("snowball"), common.Parameter.int_param("x", help="X"), common.Parameter.int_param("y", help="Y"), help="Throw snowball"),
		common.Command("say", say, varargs=common.VarArgs.NORMAL, help="Say message"),
		common.Command("joke", call_all("joke"), common.Parameter.int_param("joke_id", help="Joke ID"), help="Tell a joke"),
		common.Command("emote", call_all("emote"), common.Parameter.int_param("emote_id", help="Emote ID"), help="React an emote"),
		common.Command("mail", call_all("mail"), common.Parameter.other_penguin_name(help="Penguin name"), common.Parameter.int_param("postcard_id", help="Postcard ID"), help="Send a postcard"),
		common.Command("buy", call_all("add_item"), common.Parameter.int_param("item_id", help="Item ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy item"),
		common.Command("ai", call_all("add_item"), common.Parameter.int_param("item_id", help="Item ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy item"),
		common.Command("coins", coins, common.Parameter.int_param("amount", required=False, help="Amount"), help="Get current coins / Earn coins"),
		common.Command("ac", call_all("add_coins"), common.Parameter.int_param("amount", help="Amount"), help="Earn coins"),
		common.Command("stamp", call_all("add_stamp"), common.Parameter.int_param("stamp_id", help="Stamp ID"), varargs=common.VarArgs.MULTI_THREADED, help="Earn stamp"),
		common.Command("add_igloo", call_all("add_igloo"), common.Parameter.int_param("igloo_id", help="Igloo ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy igloo"),
		common.Command("add_furniture", call_all("add_furniture"), common.Parameter.int_param("furniture_id", help="Furniture ID"), varargs=common.VarArgs.MULTI_THREADED, help="Buy furniture"),
		common.Command("music", call_all("igloo_music"), common.Parameter.int_param("music_id", help="Music ID"), help="Set current igloo music"),
		common.Command("buddy", buddy, common.Parameter.other_penguin_name(help="Penguin name"), varargs=common.VarArgs.MULTI_THREADED, help="Send buddy request"),
		common.Command("find", find, common.Parameter.other_penguin_name(help="Penguin name"), varargs=common.VarArgs.MULTI_THREADED, help="Find buddy"),
		common.Command("follow", follow, common.Parameter.other_penguin_name(help="Penguin name"), help="Follow penguin"),
		common.Command("unfollow", call_all("unfollow"), help="Stop following"),
		common.Command("logout", logout, help="Logout"),
		common.Command("exit", logout, help="Logout"),
		common.Command("quit", logout, help="Logout")
	)
	while all(client.connected for client, dx, dy in clients_offsets):
		try:
			command, params = common.Command.read(client, commands)
		except EOFError:
			logout(clients_offsets)
			break
		command.execute(clients_offsets, params)

if __name__ == "__main__":
	main()
