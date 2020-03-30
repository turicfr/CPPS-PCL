import os
import sys
import json
import logging
import hashlib
import itertools
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

class VarArgs(object):
	NONE = 0
	SINGLE_THREADED = 1
	MULTI_THREADED = 2
	NORMAL = 3

class Command(object):
	def __init__(self, name, function, *params, **kwargs):
		if any(param.required for param in itertools.dropwhile(lambda p: p.required, params)):
			raise ValueError("all required parameters must appear before any optional parameters")
		self._name = name
		self._function = function
		self._params = params
		self._help = kwargs["help"]
		self._varargs = kwargs.get("varargs", VarArgs.NONE)

	@property
	def name(self):
		return self._name

	@property
	def help(self):
		return self._help

	@property
	def options(self):
		return [param.options for param in self._params]

	@staticmethod
	def index(*commands):
		def show_help(client, command=None):
			message = ""
			if command is None:
				message += "Available commands:\n"
				message += "{} - {}\n".format(help_command._name, help_command._help)
				message += "\n".join("{} - {}".format(command._name, command._help) for command in commands)
				message += '\n\nType help "<command>" to get help about a specific command'
			else:
				message += "{} - {}\n\n".format(command._name, command._help)
				message += "Syntax:\n"
				if command._varargs == VarArgs.NORMAL:
					message += "{} ...\n".format(command._name)
				elif command._params:
					message += "{} {}\n\n".format(command._name, " ".join(("<{}>" if param.required else "[{}]").format(param.name) for param in command._params))
					message += "Parameters:\n"
					message += "\n".join("{} - {}".format(param.name, param.help) for param in command._params)
				else:
					message += command._name
			return message
		def command_type(command):
			if command not in indexed:
				raise ValueError('Command "{}" does not exist'.format(command))
			return indexed[command]
		indexed = {command._name: command for command in commands}
		help_command = Command("help", show_help, Parameter("command", indexed.keys() + ["help"], "Command name", required=False, type=command_type), help="Show this help message")
		indexed["help"] = help_command
		return indexed

	@staticmethod
	def read(client, commands):
		while True:
			try:
				command = get_input(">>> ", {command._name: command.options for command in commands.itervalues()}, client)
			except ValueError as e:
				print e
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
			try:
				return commands[name], commands[name]._convert(params)
			except ValueError as e:
				print e
				continue

	def _convert(self, values):
		if self._varargs == VarArgs.NORMAL:
			return values
		converted = []
		for param, value in itertools.izip_longest(self._params, values):
			if param is None:
				if self._params:
					raise ValueError('Command "{}" takes at most {} parameter{} ({} given)'.format(self._name, len(self._params), "" if len(self._params) == 1 else "s", len(values)))
				else:
					raise ValueError('Command "{}" takes no parameters ({} given)'.format(self._name, len(values)))
			if value is None:
				if param.required:
					min_params = list(itertools.takewhile(lambda p: p.required, self._params))
					raise ValueError('Command "{}" takes at least {} parameter{} ({} given)'.format(self._name, len(min_params), "" if len(min_params) == 1 else "s", len(values)))
				break
			if param.type is not None:
				try:
					value = param.type(value)
				except ValueError as e:
					raise ValueError('Parameter "{}" has invalid value: "{}"'.format(param.name, value))
			converted.append(value)
		return converted

	def execute(self, client, params):
		def star(args):
			self.execute(*args)
		if len(params) > 1:
			if self._varargs == VarArgs.SINGLE_THREADED:
				for param in params:
					self.execute(client, [param])
				return
			elif self._varargs == VarArgs.MULTI_THREADED:
				pool = ThreadPool()
				pool.map(star, ((client, [param]) for param in params))
				return
		try:
			message = self._function(client, *params)
		except KeyboardInterrupt:
			print
		except LoginError as e:
			print e
		except pcl.ClientError:
			pass
		else:
			if self._function not in vars(pcl.Client) and message is not None:
				print message

class Parameter(object):
	def __init__(self, name, options, help, required=True, type=None):
		self._name = name
		self._options = options
		self._help = help
		self._required = required
		self._type = type

	@classmethod
	def logging_level(cls, help, required=True):
		def logging_level_type(level_name):
			if level_name not in logging_levels:
				raise ValueError('Unknown logging level "{}"'.format(level_name))
			return logging_levels[level_name], level_name
		logging_levels = {
			"all": logging.NOTSET,
			"debug": logging.DEBUG,
			"info": logging.INFO,
			"warning": logging.WARNING,
			"error": logging.ERROR,
			"critical": logging.CRITICAL
		}
		return cls("level", logging_levels.keys(), required=required, type=logging_level_type, help=help)

	@classmethod
	def int_param(cls, name, help, required=True):
		return cls(name, [], required=required, type=int, help=help)

	@classmethod
	def penguin_name(cls, help, required=True):
		return cls("penguin_name", lambda c: [penguin.name for penguin in c.penguins.itervalues()], required=required, help=help)

	@classmethod
	def other_penguin_name(cls, help, required=True):
		return cls("penguin_name", lambda c: [penguin.name for penguin in c.penguins.itervalues() if penguin.id != c.id], required=required, help=help)

	@property
	def name(self):
		return self._name

	@property
	def options(self):
		return self._options

	@property
	def help(self):
		return self._help

	@property
	def required(self):
		return self._required

	@property
	def type(self):
		return self._type

def list_completer(options):
	def complete(text, state):
		return [option for option in options if option.startswith(text)][state]
	return complete

def shell_completer(client, options):
	def resolve(options, line):
		for i, option in enumerate(line):
			if isinstance(options, dict):
				if option not in options:
					return []
				options = options[option]
				continue
			if len(line) - i >= len(options):
				return []
			if callable(options[len(line) - i]):
				return options[len(line) - i](client)
			return options[len(line) - i]
		if isinstance(options, dict):
			return options.keys()
		if not options:
			return []
		if callable(options[0]):
			return options[0](client)
		return options[0]
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
		line = raw_input(prompt)
		if shell_client is None:
			return line
		return split(line)
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
	if "host" in servers[cpps]:
		login_host = game_host = servers[cpps]["host"]
		login_port = servers[cpps]["login"]
		game_port = servers[cpps]["servers"][server]
	else:
		if ":" in servers[cpps]["login"]:
			login_host, login_port = servers[cpps]["login"].split(":")
			login_port = int(login_port)
		else:
			login_host, login_port = servers[cpps]["login"], None
		game_host, game_port = servers[cpps]["servers"][server].split(":")
		game_port = int(game_port)
	magic = servers[cpps].get("magic")
	single_quotes = servers[cpps].get("single_quotes")
	recaptcha = servers[cpps].get("recaptcha")
	if recaptcha is None:
		origin = None
		sitekey = None
	else:
		origin = recaptcha["origin"]
		sitekey = recaptcha["sitekey"]
	return pcl.Client(login_host, login_port, game_host, game_port, magic, single_quotes, origin, sitekey, logger)

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
		del penguins[cpps][user]
		set_json("penguins", penguins)
		print "Removed {}".format(user)
