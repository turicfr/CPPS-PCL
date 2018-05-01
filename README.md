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
4. Choose a server (if you didn't do that in the command line)
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
- log __[level]__ - sets log level (single-login only) / toggles log on/off (single-login only), where __[level]__ is one of the following:
	- all - all log messages (may be really verbose).
	- debug - all relevant messages for debugging (e.g. sent and received packets etc.) and below.
	- info - all messages of higher-level activities (e.g. walking, talking etc.) and below.
	- warning - all warning messages (e.g. unhandled received packets) and below.
	- error - all error messages (e.g. could not add item) and below. This is the default log level.
	- critical - all major error messages (e.g. connection lost).
- internal - prints current internal room id (single-login only)
- id [__[name]__] - prints your id (single-login only) / prints the id of penguin named __[name]__.
- name [__[id]__] - prints your name (single-login only) / prints the name of penguin with id __[id]__.
- room [__[id/name]__] - prints current room (single-login only) / goes to room with id __[id]__ _or_ room named __[name]__.
- igloo [__[id/name]__] - goes to your igloo (single-login only) / goes to igloo of penguin with id __[id]__ _or_ penguin named __[name]__.
- penguins - prints all penguins in current room (single-login only).
- color [__[id]__] - prints current color (single-login only) / equips color with id __[id]__.
- head [__[id]__] - prints current head item (single-login only) / equips head item with id __[id]__.
- face [__[id]__] - prints current face item (single-login only) / equips face item with id __[id]__.
- neck [__[id]__] - prints current neck item (single-login only) / equips neck item with id __[id]__.
- body [__[id]__] - prints current body item (single-login only) / equips body item with id __[id]__.
- hand [__[id]__] - prints current hand item (single-login only) / equips hand item with id __[id]__.
- feet [__[id]__] - prints current feet item (single-login only) / equips feet item with id __[id]__.
- pin [__[id]__] - prints current pin (single-login only) / equips pin with id __[id]__.
- background [__[id]__] - prints current background (single-login only) / equips background with id __[id]__.
- inventory - prints current inventory (single-login only).
- stamps __[id/name]__ - prints all earned stamps of penguin with id __[id]__ _or_ penguin named __[name]__ (single-login only).
- walk __[x]__ __[y]__ - walks to (__[x]__, __[y]__).
- dance - dances.
- wave - waves.
- sit __[dir]__ - sits in direction __[dir]__, where __[dir]__ is one of the following:
	- se - south east
	- e - east
	- ne - north east
	- n - north
	- nw - north west
	- w - west
	- sw - south west
	- s - south (default)
- snowball __[x]__ __[y]__ - throws a snowball to (__[x]__, __[y]__).
- say __[msg]__ - says __[msg]__.
- joke __[id]__ - tells a joke with id __[id]__.
- emote __[id]__ - reacts an emote with id __[id]__.
- mail __[id/name]__ __[postcard]__ - sends a poscard with id __[postcard]__ to a penguin with id __[id]__ _or_ penguin named __[name]__.
- buy / ai __[id]__ - buys an item with id __[id]__.
- coins [__[amount]__] - prints current coins (single-login only) / earns __[amount]__ coins.
- ac  __[amount]__ - earns __[amount]__ coins.
- stamp __[id]__ - earns stamp with id __[id]__.
- add_igloo __[id]__ - buys igloo with id __[id]__.
- add_furniture __[id]__ - buys furniture with id __[id]__.
- music __[id]__ - sets igloo music to __[id]__.
- buddy __[id/name]__ - sends a buddy request to a penguin with id __[id]__ _or_ penguin named __[name]__.
- find __[id/name]__ - finds location of buddy with id __[id]__ _or_ buddy named __[name]__ (single-login only).
- follow __[id/name]__ [__[dx]__ __[dy]__] - prints currently followed penguin (single-login only) / follows a penguin with id __[id]__ _or_ penguin named __[name]__ with no offset / follows a penguin with id __[id]__ _or_ penguin named __[name]__ with offset (__[dx]__, __[dy]__).
- unfollow - disables follow.
- logout / exit / quit - logouts from the game.

## Tips and Tricks
- Define more CPPSs and servers in json/servers.json
- Define more shapes in json/shapes.json
