import sys
import msvcrt
import os
import json
import client
		
def get_password(cpps, user, remember = True):
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	try:
		with open(filename) as file:
			data = json.load(file)
	except:
		data = {}
	if cpps in data and user in data[cpps]:
		return data[cpps][user]
	
	print "Password: ",
	password = ""
	while True:
		c = msvcrt.getch()
		if c == '\r' or c == '\n':
			break
		if c == '\b':
			if len(password) > 0:
				sys.stdout.write("\b \b")
				password = password[:-1]
		else:
			sys.stdout.write('*')
			password += c
	print ""
	
	if remember and raw_input("Remember? [y/N] ") == "y":
		if not cpps in data:
			data[cpps] = {}
		data[cpps][user] = password
		with open(filename, "w") as file:
			json.dump(data, file)
	return password

def help(params):
	print """HELP"""

def room(params):
	client.room(params[0])
	
def color(params):
	client.update_color(params[0])

def head(params):
	client.update_head(params[0])

def face(params):
	client.update_face(params[0])

def neck(params):
	client.update_neck(params[0])

def body(params):
	client.update_body(params[0])

def hand(params):
	client.update_hand(params[0])

def feet(params):
	client.update_feet(params[0])

def pin(params):
	client.update_pin(params[0])

def background(params):
	client.update_background(params[0])

def walk(params):
	client.walk(params[0], params[1])

def dance(params):
	client.dance()

def wave(params):
	client.wave()

def sit(params):
	client.sit(params[0])

def snowball(params):
	client.snowball(params[0], params[1])

def say(params):
	client.say(' '.join(params))

def joke(params):
	client.joke(params[0])

def emote(params):
	client.emote(params[0])

def item(params):
	client.add_item(params[0])

def follow(params):
	client.follow(' '.join(params))

def unfollow(params):
	client.unfollow()

def logout(params):
	client.logout()
	sys.exit(0)

cpps = "cpr"
filename = os.path.join(os.path.dirname(__file__), "json/servers.json")
with open(filename) as file:
	data = json.load(file)
if not cpps in data:
	sys.exit("CPPS not found")
data = data[cpps]

user = raw_input("Username: ")
password = get_password(cpps, user)
server = raw_input("Server: ").lower()

ip = data["ip"]
login = data["login"]
port = data["servers"]
if not server in port:
	sys.exit("Server not found")
port = port[server]

client = client.Client(ip, login, port)
if not client.log:
	print "Connecting..."
connected = client.connect(user, password)
if connected:
	print "Connected!"
	
	commands = {
		"help": help,
		"room": room,
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
		"item": item,
		"follow": follow,
		"unfollow": unfollow,
		"logout": logout
	}
	
	while True:
		print ">>>",
		cmd = raw_input().split(' ')
		name = cmd[0]
		params = cmd[1:]
		if name in commands:
			commands[name](params)
		else:
			print "command '" + name + "' doesn't exist"
else:
	sys.exit("Failed to connect")