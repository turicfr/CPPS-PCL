import os
import sys
import json
import hashlib
from shlex import split
from getpass import getpass
from multiprocessing.pool import ThreadPool
import client as pcl
try:
	import readline
except ImportError:
	readline = None

class LoginError(Exception):
	def __init__(self, message=""):
		super(LoginError, self).__init__(message)

class Command(object):
	SINGLE_THREAD = 1
	MULTI_THREADS = 2

	def __init__(self, name, function, params, multiple_args=0):
		self._name = name
		self._function = function
		self._params = params
		self._multiple_args = multiple_args

	@staticmethod
	def commands(commands):
		return {command.name: command for command in commands}

	@staticmethod
	def read(client, commands):
		while True:
			try:
				command = get_input(">>> ", {command.name: command._params for command in commands.itervalues()}, client)
			except ValueError as e:
				print e.message
				continue
			except KeyboardInterrupt:
				print
				continue
			if not command:
				continue
			name, params = command[0], command[1:]
			if name not in commands:
				print 'Command "{}" does not exist'.format(name)
				continue
			break
		return commands[name], params

	@property
	def name(self):
		return self._name

	def execute(self, client, params):
		def star(args):
			self.execute(*args)
		if self._multiple_args and len(params) > 1:
			if self._multiple_args == self.MULTI_THREADS:
				pool = ThreadPool()
				pool.map(star, ((client, [param]) for param in params))
			else:
				for param in params:
					self.execute(client, [param])
			return
		try:
			message = self._function(client, *params)
		except TypeError as e:
			if self._function.__name__ + "() takes" not in e.message:
				raise
			print 'Command "{}" does not take {} arguments'.format(self.name, len(params))
		except KeyboardInterrupt:
			print
		except LoginError as e:
			print e.message
		except pcl.ClientError:
			pass
		else:
			if self._function not in vars(pcl.Client) and message is not None:
				print message

def list_completer(options):
	def complete(text, state):
		return [option for option in options if option.startswith(text)][state]
	return complete

def shell_completer(client, options):
	def resolve(options, line):
		for i, option in enumerate(line):
			if option is None:
				continue
			if isinstance(options, dict):
				if option not in options:
					return []
				options = options[option]
			elif isinstance(options, list):
				if len(line) - i >= len(options):
					return []
				if callable(options[len(line) - i]):
					return options[len(line) - i](client)
				return options[len(line) - i]
			else:
				assert False, "options must be either dict or list"
		if isinstance(options, dict):
			return options.keys()
		if isinstance(options, list):
			if not options:
				return []
			if callable(options[0]):
				return options[0](client)
			return options[0]
		assert False, "options must be either dict or list"
	def complete(text, state):
		line_buffer = readline.get_line_buffer()
		try:
			line = split(line_buffer)
		except ValueError:
			return None
		if not line:
			line = [""]
		index = len(line)
		if not line_buffer.endswith(tuple(readline.get_completer_delims())):
			index -= 1
		return [option + " " for option in resolve(options, line[:index]) if option.startswith(text)][state]
	return complete

def get_input(prompt=None, options=None, shell_client=None):
	if readline is not None and options is not None:
		completer_delims = readline.get_completer_delims()
		completer = readline.get_completer()
		readline.parse_and_bind("tab: complete")
		if shell_client is None:
			readline.set_completer_delims("")
			readline.set_completer(list_completer(options))
		else:
			readline.set_completer_delims(" ")
			readline.set_completer(shell_completer(shell_client, options))
	try:
		line = raw_input() if prompt is None else raw_input(prompt)
		return line if shell_client is None else split(line)
	finally:
		if readline is not None and options is not None:
			readline.set_completer_delims(completer_delims)
			readline.set_completer(completer)

def get_json(filename):
	filename = os.path.join(os.path.dirname(__file__), "json", filename + ".json")
	try:
		with open(filename) as file:
			return json.load(file)
	except (IOError, ValueError):
		return {}

def set_json(filename, data):
	filename = os.path.join(os.path.dirname(__file__), "json", filename + ".json")
	try:
		with open(filename, "w") as file:
			json.dump(data, file)
	except IOError:
		return False
	return True

# TODO
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

def get_cpps(servers, cpps=None):
	if cpps is None:
		cpps = get_input("CPPS: ", servers.keys())
	cpps = cpps.lower()
	if cpps not in servers:
		raise LoginError('CPPS "{}" not found'.format(cpps))
	return cpps

def get_user(penguins, cpps, user=None):
	if user is None:
		user = get_input("Username: ", penguins.get(cpps, {}).keys())
	return user.lower()

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
		raise LoginError('Server "{}" not found'.format(server))
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
	return pcl.Client(login_ip, login_port, game_ip, game_port, magic, single_quotes, logger)

def get_penguin(cpps=None, server=None, user=None, remember=None, client=None):
	servers = get_json("servers")
	penguins = get_json("penguins")
	try:
		cpps = get_cpps(servers, cpps)
		user = get_user(penguins, cpps, user)
		password, encrypted = get_password(penguins, cpps, user, remember)
		server = get_server(servers, cpps, server)
	except (KeyboardInterrupt, EOFError):
		raise LoginError()
	return cpps, server, user, password, encrypted, get_client(servers, cpps, server) if client is None else client

def remove_penguin(cpps, user, penguins=None, ask=True):
	if penguins is None:
		penguins = get_json("penguins")
	if cpps in penguins and user in penguins[cpps] and (not ask or get_input("Remove penguin? [y/N] ", ["y", "N"]) == "y"):
		print "Removing {}...".format(user)
		del penguins[cpps][user]
		set_json("penguins", penguins)
