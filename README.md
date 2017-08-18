# CPPS-PCL
An intercative Penguin Client Library for Club Penguin Private Servers written in Python.

**Warning:** High ban risk - Do not use with your own main penguin.

**Note:** This PCL does NOT work for Club Penguin Rewritten on purpose, and any request to change it will not be accepted.

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
1. Run login.py:
```
python login.py
```
2. Enter your username and password
3. Choose a server
4. Waddle on!

### Multi-Login
1. Run multi.py:
```
python multi.py
```
2. Choose a server
3. Choose a shape (defined in json/shapes.json)
4. Enter your usernames and passwords (as many as needed for the shape)
5. Waddle on!

## Commands
- help - prints "HELP" (will be done in the future)
- log - toggles log on/off (single-login only)
- id __[name]__ - prints your id (single-login only) / prints the id of penguin named __[name]__ (single-login only)
- room __[id/name]__ - goes to room with id __[id]__ _or_ goes to room named __[name]__ / prints current room (single-login only)
- color __[id]__ - equips color with id __[id]__ / prints current color (single-login only)
- head __[id]__ - equips head item with id __[id]__ / prints current head item (single-login only)
- face __[id]__ - equips face item with id __[id]__ / prints current face item (single-login only)
- neck __[id]__ - equips neck item with id __[id]__ / prints current neck item (single-login only)
- body __[id]__ - equips body item with id __[id]__ / prints current body item (single-login only)
- hand __[id]__ - equips hand item with id __[id]__ / prints current hand item (single-login only)
- feet __[id]__ - equips feet item with id __[id]__ / prints current feet item (single-login only)
- pin __[id]__ - equips pin with id __[id]__ / prints current pin (single-login only)
- background __[id]__ - equips background with id __[id]__ / prints current background (single-login only)
- walk __[x]__ __[y]__ - walks to (__[x]__, __[y]__)
- dance - dances
- wave - waves
- sit __[dir]__ - sits in direction __[dir]__, where __[dir]__ is one of the following:
  - se - south east
  - e - east
  - ne - north east
  - n - north
  - nw - north west
  - w - west
  - sw - south west
  - s - south (default)
- snowball __[x]__ __[y]__ - throws a snowball to (__[x]__, __[y]__)
- say __[msg]__ - says __[msg]__
- joke __[id]__ - says joke with id __[id]__
- emote __[id]__ - says an emote with id __[id]__
- buy __[id]__ - buys item with id __[id]__
- coins __[amount]__ - earns __[amount]__ coins / prints current coins (single-login only)
- stamp __[id]__ - earns stamp with id __[id]__
- add_igloo __[id]__ - buys igloo with id __[id]__
- furniture __[id]__ - buys furniture with id __[id]__
- follow __[name]__ __[dx]__ __[dy]__ - follows a penguin named __[name]__ with offset (__[dx]__, __[dy]__) / follows a penguin named __[name]__ with no offset / prints currently followed penguin
- unfollow - disables follow
- logout - logouts from the game

## Tips and Tricks
- Edit json/servers.json in order to define more CPPSs and servers (ports can be found using a packet sniffer)
- Define more shapes in json/shapes.json
- While using multi-login, the main penguin can command the bots by saying messages starting with "!".

### Direct Commands
- !ai __[id]__ - like buy command
- !ac __[amount]__ - like coins command
- !ping - response "pong"
