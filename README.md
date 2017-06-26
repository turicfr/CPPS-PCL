# CPPS-PCL
An intercative Penguin Client Library for Club Penguin Private Servers written in Python.

**Warning:** High ban risk - Do not use with your own main penguin.

This PCL contains 2 modes:

### 1. Single-Login

A simple login with one penguin.

### 2. Multi-Login

A complex login with multiple penguins managed by a certain shape.

## Requirements
- Python 2.x or 3.x
- Internet connection

## Usage

### Single-Login
1. Run login.py
2. Enter your username and password
3. Choose a server
4. Waddle on!

### Multi-Login
1. Run multi.py
2. Choose a server
3. Choose a shape (defined in json/shapes.json)
4. Enter your usernames and passwords (as many as needed for the shape)
5. Waddle on!

## Commands
- help - prints "HELP" (will be done in the future)
- log - toggles log on/off (single-login only)
- id [name] - prints your id (single-login only) / prints the id of penguin [name] (single-login only)
- coins - prints current coins (single-login only)
- room [id] - goes to room with id [id] / prints current room (single-login only)
- color [id] - equips color with id [id] / prints current color (single-login only)
- head [id] - equips head item with id [id] / prints current head item (single-login only)
- face [id] - equips face item with id [id] / prints current face item (single-login only)
- neck [id] - equips neck item with id [id] / prints current neck item (single-login only)
- body [id] - equips body item with id [id] / prints current body item (single-login only)
- hand [id] - equips hand item with id [id] / prints current hand item (single-login only)
- feet [id] - equips feet item with id [id] / prints current feet item (single-login only)
- pin [id] - equips pin with id [id] / prints current pin (single-login only)
- background [id] - equips background with id [id] / prints current background (single-login only)
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
- logout - logouts from the game

## Tips and Tricks
- Edit json/servers.json in order to define more CPPSs and servers (ports can be found using a packet sniffer)
- Define more shapes in json/shapes.json
