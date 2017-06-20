# CPPS-PCL
A simple Penguin Client Library for Club Penguin Private Servers written in Python

**Warning:** High ban risk - Do not use with your own main penguin.

# Requirements
- Python 2.x or 3.x
- Internet connection

# Usage
1. Run login.py
2. Enter your username and password
3. Choose a server
4. Waddle on!

# Commands
- help - prints "HELP" (will be done in the future)
- room [id] - goes to room with id [id]
- color [id] - equips color with id [id]
- head [id] - equips head item with id [id]
- face [id] - equips face item with id [id]
- neck [id] - equips neck item with id [id]
- body [id] - equips body item with id [id]
- hand [id] - equips hand item with id [id]
- feet [id] - equips feet item with id [id]
- pin [id] - equips pin with id [id]
- background [id] - equips background with id [id]
- walk [x] [y] - walks to ([x], [y])
- dance - dances
- wave - waves
- sit [dir] - sits in direction [dir], where [dir] is one of the following:
  - se - south east
  - e - east
  - ne - north east
  - n - north
  - nw - north west
  - w - west
  - sw - south west
  - s - south
- snowball [x] [y] - throws a snowball to ([x], [y])
- say [message] - says [message]
- joke [id] - says joke with id [id]
- emote [id] - says an emote with id [id]
- item [id] - adds items with id [id]
- follow [name] - follows a penguin named [name]
- unfollow - disables follow
- logout - logouts

# Tips and Tricks
- Edit json/servers.json in order to define more CPPSs and servers (ports can be found using a packet sniffer)
- Turn on log by changing line 129 in login.py to 'client = client.Client(ip, login, port, True)'
