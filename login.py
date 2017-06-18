import sys
import os
import json
import client

def command(cmd, client):
	words = cmd.split(' ')
	name = words[0]
	params = words[1:]
	if name == "help":
		print "HELP"
	elif name == "walk":
		client.walk(params[0], params[1])
	elif name == "say":
		client.say(' '.join(params))
	elif name == "joke":
		client.joke(params[0])
	elif name == "room":
		client.room(params[0])
	elif name == "item":
		client.add_item(params[0])
	elif name == "follow":
		client.follow(' '.join(params))
	elif name == "unfollow":
		client.unfollow()
	elif name == "logout":
		client.logout()
		sys.exit(0)
		
def get_password(cpps, user, remember = True):
	filename = os.path.join(os.path.dirname(__file__), "json/penguins.json")
	try:
		with open(filename) as file:
			data = json.load(file)
	except:
		data = {}
	if cpps in data and user in data[cpps]:
		return data[cpps][user]
	password = raw_input("Password: ")
	if remember and raw_input("Remember? [y/n] ") == "y":
		if not cpps in data:
			data[cpps] = {}
		data[cpps][user] = password
		with open(filename, "w") as file:
			json.dump(data, file)
	return password

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
connected = client.connect(user, password)
if connected:
	print "Connected!"
	while True:
		cmd = raw_input()
		command(cmd, client)