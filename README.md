# CPPS-PCL
A Penguin Client Library for Club Penguin Private Servers written in Python.

**Warning:** High ban risk - Do not use with your own main penguin.

This PCL contains an API, alongside two CLI interactive modes:

### 1. Single-Login

A simple login with one penguin.

### 2. Multi-Login

A complex login with multiple penguins managed by a certain shape.

## Requirements
- Python 2.x
- Internet connection

## Usage

### API
TODO

### Single-Login
1. Run login.py:
```
python login.py [-r yes|no|ask] [<cpps>] [<server>] [<username>]

Options:
-r  Remember password in the future
```
2. Choose a server (if you didn't do that in the command line)
3. Enter your username and password (if you didn't do that in the command line)
4. Choose a server
5. Waddle on!

### Multi-Login
1. Run multi.py:
```
python multi.py [-r yes|no|ask] [<cpps>] [<server>] [<shape>]

Options:
-r  Remember password in the future
```
2. Choose a server (if you didn't do that in the command line)
3. Choose a shape (defined in json/shapes.json, if you didn't do that in the command line)
4. Enter your usernames and passwords (as many as needed for the shape)
5. Waddle on!

## Interactive Commands
- help - prints "HELP" (will be done in the future)
- log __[level]__ - sets log level / toggles log on/off (single-login only), where __[level]__ is one of the following:
	- all - all log messages (may be really verbose).
	- debug - all relevant messages for debugging (e.g. sent and received packets etc.) and below.
	- info - all messages of higher-level activities (e.g. walking, talking etc.) and below.
	- warning - all warning messages (e.g. unhandled received packets) and below.
	- error - all error messages (e.g. could not add item) and below. This is the default log level.
	- cricital - all major error messages (e.g. connection lost).
- internal - prints current internal room id (single-login only)
- id __[name]__ - prints your id (single-login only) / prints the id of penguin named __[name]__ (single-login only)
- name __[id]__ - prints the name of penguin with id __[id]__ (single-login only)
- room __[id/name]__ - goes to room with id __[id]__ _or_ goes to room named __[name]__ / prints current room (single-login only)
- igloo __[id/name]__ - goes to igloo of penguin with id __[id]__ (single-login only)
- penguins - prints all penguins in current room (single-login only)
- color __[id]__ - equips color with id __[id]__ / prints current color (single-login only)
- head __[id]__ - equips head item with id __[id]__ / prints current head item (single-login only)
- face __[id]__ - equips face item with id __[id]__ / prints current face item (single-login only)
- neck __[id]__ - equips neck item with id __[id]__ / prints current neck item (single-login only)
- body __[id]__ - equips body item with id __[id]__ / prints current body item (single-login only)
- hand __[id]__ - equips hand item with id __[id]__ / prints current hand item (single-login only)
- feet __[id]__ - equips feet item with id __[id]__ / prints current feet item (single-login only)
- pin __[id]__ - equips pin with id __[id]__ / prints current pin (single-login only)
- background __[id]__ - equips background with id __[id]__ / prints current background (single-login only)
- inventory - prints current inventory (single-login only)
- stamps - prints current all earned stamps (single-login only)
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
- joke __[id]__ - says a joke with id __[id]__
- emote __[id]__ - says an emote with id __[id]__
- mail __[postcard]__ __[name]__ - sends a penguin named __[name]__ a poscard with id __[postcard]__
- buy / ai __[id]__ - buys an item with id __[id]__
- coins __[amount]__ - earns __[amount]__ coins / prints current coins (single-login only)
- ac  __[amount]__ - earns __[amount]__ coins
- stamp __[id]__ - earns stamp with id __[id]__
- add_igloo __[id]__ - buys igloo with id __[id]__
- add_furniture __[id]__ - buys furniture with id __[id]__
- music __[id]__ - sets igloo music to __[id]__
- buddy __[name]__ - sends a buddy request to a penguin named __[name]__
- follow __[name]__ __[dx]__ __[dy]__ - follows a penguin named __[name]__ with offset (__[dx]__, __[dy]__) / follows a penguin named __[name]__ with no offset / prints currently followed penguin
- unfollow - disables follow
- logout / exit / quit - logouts from the game

## Tips and Tricks
- Define more CPPSs and servers in json/servers.json
- Define more shapes in json/shapes.json
