# CPPS-PCL
A simple Penguin Client Library for Club Penguin Private Servers written in Python

**Warning:** High ban risk - Do not use with your own main penguin.

## Requirements
- Python 2.x or 3.x
- Internet connection

## Usage
1. Run login.py
2. Enter your username and password
3. Choose a server
4. Waddle on!

## Commands
- help - prints "HELP" (will be done in the future)
- log - toggles log on/off
- id - prints your id
- coins - prints current coins
- room [id] - goes to room with id [id] / prints current room
- color [id] - equips color with id [id] / prints current color
- head [id] - equips head item with id [id] / prints current head item
- face [id] - equips face item with id [id] / prints current face item
- neck [id] - equips neck item with id [id] / prints current neck item
- body [id] - equips body item with id [id] / prints current body item
- hand [id] - equips hand item with id [id] / prints current hand item
- feet [id] - equips feet item with id [id] / prints current feet item
- pin [id] - equips pin with id [id] / prints current pin
- background [id] - equips background with id [id] / prints current background
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
  - s - south (default)
- snowball [x] [y] - throws a snowball to ([x], [y])
- say [message] - says [message]
- joke [id] - says joke with id [id]
- emote [id] - says an emote with id [id]
- buy [id] - buys item with id [id]
- follow [name] - follows a penguin named [name] / prints currently followed penguin
- unfollow - disables follow
- logout - logouts (may take few minutes)

## Tips and Tricks
- Edit json/servers.json in order to define more CPPSs and servers (ports can be found using a packet sniffer)
