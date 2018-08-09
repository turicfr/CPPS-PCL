# CPPS-PCL

A Penguin Client Library for Club Penguin Private Servers written in Python.

**Warning:** High ban risk!

* [Introduction](#introduction)
* [Requirements](#requirements)
* [Usage](#usage)
* [Supported CPPSs](#supported-cppss)
* [Interactive Commands](#interactive-commands)
* [FAQ](#faq)

## Introduction

This PCL contains an API, alongside two CLI interactive modes:

### 1. Single-Login

A simple login with one penguin.

### 2. Multi-Login

A complex login with multiple penguins managed by a certain shape.

## Requirements
* Python 2.x
* Internet connection
* _For Club Penguin Rewritten_: [cefpython](https://github.com/cztomczak/cefpython) (can be installed with: `pip install cefpython3`)
* _For Club Penguin Online_: [PyCrypto](https://pypi.org/project/pycrypto/) (can be installed with: `pip install pycrypto`, and [here](http://www.voidspace.org.uk/python/modules.shtml#pycrypto) for Windows)
* _For Penguin Oasis_: [Requests](http://docs.python-requests.org/) (can be installed with: `pip install requests`)

## Usage

### API
TODO

### Single-Login
1. Run `login.py`:
```
python login.py [-r {yes,no,ask}] [<cpps>] [<server>] [<username>]

Options:
	-r  Remember password in the future
```
2. Choose a server (if not already specified in the command line)
3. Enter your username and password (if not already specified in the command line)
4. Choose a server (if not already specified in the command line)
5. Waddle on!

### Multi-Login
1. Run `multi.py`:
```
python multi.py [-r {yes,no,ask}] [<cpps>] [<server>] [<shape>]

Options:
	-r  Remember password in the future
```
2. Choose a server (if not already specified in the command line)
3. Choose a shape (if not already specified in the command line)
4. Enter your usernames and passwords (as many as needed for the shape)
5. Waddle on!

## Supported CPPSs
Currently 16 different servers are supported, which can also be found in [`json/servers.json`](https://github.com/relrelb/CPPS-PCL/blob/master/json/servers.json):
* `reborn` - [Club Penguin Reborn](https://cpreborn.com/)
* `me` - [CPPS Me](http://cpps.me/)
* `nation` - [Penguin Nation](http://penguins.coffee/)
* `io` - [CPPS IO](https://cpps.io/)
* `cpbr` - [Club Penguin Brasil](https://www.clubpenguinbrasil.pw/)
* `free` - [Free Penguin](http://freepenguin.xyz/)
* `super` - [Super CPPS](https://supercpps.com/)
* `cpo` - [Club Penguin Online](https://clubpenguinonline.com/)
* `hangout` - [Penguin Hangout](https://penguinhangout.pw/)
* `reversed` - [Club Penguin Reversed](https://cpreversed.me/)
* `aventure pingouin` - [Aventure Pingouin](https://aventurepingouin.com/)
* `one` - [CPPS One](https://cpps.one/)
* `cpr` - [Club Penguin Rewritten](https://cprewritten.net/)
* `snowy island` - [Snowy Island](https://snowyisland.net/)
* `again` - [Club Penguin Again](https://www.clubpenguinagain.com/)
* `oasis` - [Club Penguin Oasis](https://penguinoasis.com/)

If you want support for a new CPPS, please [open an issue](https://github.com/relrelb/CPPS-PCL/issues/new) regarding it.

## Interactive Commands
| Mode | Command | Parameters | Description |
| ---- | ------- | ---------- | ----------- |
| Both | `help` | _None_ | Get all available commands. |
| Both | `help` | `command` | Get help about command named `command`. |
| Single-Login only | `log` | _None_ | Toggle logging on/off. |
| Single-Login only | `log` | `level` | Set logging level to `level`.<br>`level` must be one of the following:<ul><li>`all` - Logs all messages below.</li><li>`debug` - Logs debug messages such as sent and received packets, and below.</li><li>`info` - Logs higher-level messages such as walking, talking etc., and below.</li><li>`warning` - Logs warning messages such as unhandled packets, and below.</li><li>`error` - Logs failure messages such as "Could not add item", and below (default).</li><li>`critical` - Logs fatal error messages such as "Connection lost".</li></ul> |
| Both | `internal` | _None_ | Get current internal room ID. |
| Single-Login only | `id` | _None_ | Get current penguin ID. |
| Both | `id` | `penguin_name...` | Get ID of penguin(s) named `penguin_name`. |
| Both | `name` | _None_ | Get current penguin name. |
| Both | `name` | `penguin_id...` | Get name of penguin(s) with ID `penguin_id`. |
| Both | `room` | _None_ | Get current room name. |
| Both | `room` | `room_id` | Go to room with ID `room_id`. |
| Both | `room` | `room_name` | Go to room named `room_name`. |
| Single-Login only | `igloo` | _None_ | Go to your igloo. |
| Both | `igloo` | `penguin_id` | Go to igloo of penguin with ID `penguin_id`. |
| Both | `igloo` | `penguin_name` | Go to igloo of penguin named `penguin_name`. |
| Single-Login only | `penguins` | _None_ | Get all penguins in current room. |
| Both | `color` | _None_ | Get current color item ID. |
| Both | `color` | `item_id` | Equip color item with ID `item_id`. |
| Both | `head` | _None_ | Get current head item ID. |
| Both | `head` | `item_id` | Equip head item with ID `item_id`. |
| Both | `face` | _None_ | Get current face item ID. |
| Both | `face` | `item_id` | Equip face item with ID `item_id`. |
| Both | `neck` | _None_ | Get current neck item ID. |
| Both | `neck` | `item_id` | Equip neck item with ID `item_id`. |
| Both | `body` | _None_ | Get current body item ID. |
| Both | `body` | `item_id` | Equip body item with ID `item_id`. |
| Both | `hand` | _None_ | Get current hand item ID. |
| Both | `hand` | `item_id` | Equip hand item with ID `item_id`. |
| Both | `feet` | _None_ | Get current feet item ID. |
| Both | `feet` | `item_id` | Equip feet item with ID `item_id`. |
| Both | `pin` | _None_ | Get current pin item ID. |
| Both | `pin` | `item_id` | Equip pin item with ID `item_id`. |
| Both | `background` | _None_ | Get current background item ID. |
| Both | `background` | `item_id` | Equip background item with ID `item_id`. |
| Single-Login only | `clothes` | _None_ | Get all currently equipped item IDs. |
| Both | `clothes` | `penguin_id...` | Get all currently equipped item IDs of penguin(s) with ID `penguin_id`. |
| Both | `clothes` | `penguin_name...` | Get all currently equipped item IDs of penguin(s) named `penguin_name`. |
| Both | `inventory` | _None_ | Get current inventory. |
| Single-Login only | `buddies` | _None_ | Get all current buddies. |
| Single-Login only | `stamps` | _None_ | Get all currently earned stamps. |
| Single-Login only | `stamps` | `penguin_id...` | Get all currently earned stamps by penguin(s) with ID `penguin_id`. |
| Single-Login only | `stamps` | `penguin_name...` | Get all currently earned stamps by penguin(s) named `penguin_name`. |
| Both | `walk` | `x` `y` | Walk to (`x`, `y`). |
| Both | `dance` | _None_ | Dance. |
| Both | `wave` | _None_ | Wave. |
| Both | `sit` | _None_ | Sit in direction South. |
| Both | `sit` | `direction` | Sit in direction `direction`.<br>`direction` must be one of the following:<ul><li>`se` - South East.</li><li>`e` - East.</li><li>`ne` - North East.</li><li>`n` - North.</li><li>`nw` - North West.</li><li>`w` - West.</li><li>`sw` - South West.</li><li>`s` - South.</li></ul> |
| Both | `snowball` | `x` `y` | Throw a snowball to (`x`, `y`). |
| Both | `say` | `message...` | Say `message`. |
| Both | `joke` | `joke_id` | Tell joke with ID `joke_id`. |
| Both | `emote` | `emote_id` | React emote with ID `emote_id`. |
| Both | `mail` | `penguin_id` `postcard_id` | Send to a penguin with ID `penguin_id` a postcard with ID `postcard_id`. |
| Both | `mail` | `penguin_name` `postcard_id` | Send to a penguin named `penguin_name` a postcard with ID `postcard_id`. |
| Both | `buy` | `item_id...` | Buy item(s) with ID `item_id`. |
| Both | `ai` | `item_id...` | Buy item(s) with ID `item_id`. |
| Both | `coins` | _None_ | Get current coins. |
| Both | `coins` | `amount` | Earn `amount` coins. |
| Both | `ac` | `amount` | Earn `amount` coins. |
| Both | `stamp` | `stamp_id...` | Earn stamp(s) with ID `stamp_id`. |
| Both | `add_igloo` | `igloo_id...` | Buy igloo(s) with ID `igloo_id`. |
| Both | `add_furniture` | `furniture_id...` | Buy furniture(s) with ID `furniture_id`. |
| Both | `music` | `music_id` | Set current igloo music to `music_id`. |
| Both | `buddy` | `penguin_id...` | Send a buddy request to penguin(s) with ID `penguin_id`. |
| Both | `buddy` | `penguin_name...` | Send a buddy request to penguin(s) named `penguin_name`. |
| Single-Login only | `find` | `penguin_id...` | Find room of buddy/buddies with ID `penguin_id`. |
| Single-Login only | `find` | `penguin_name...` | Find room of buddy/buddies named `penguin_name`. |
| Single-Login only | `follow` | _None_ | Get currently followed penguin. |
| Both | `follow` | `penguin_id` | Follow a penguin with ID `penguin_id`. |
| Both | `follow` | `penguin_name` | Follow a penguin named `penguin_name`. |
| Both | `follow` | `penguin_id` `dx` `dy` | Follow a penguin with ID `penguin_id` with offset (`dx`, `dy`). |
| Both | `follow` | `penguin_name` `dx` `dy` | Follow a penguin named `penguin_name` with offset (`dx`, `dy`). |
| Both | `unfollow` | _None_ | Stop following. |
| Both | `logout` | _None_ | Logout. |
| Both | `exit` | _None_ | Logout. |
| Both | `quit` | _None_ | Logout. |

## FAQ

### I double-clicked `login.py` and a command prompt appeared and then closed, what should I do?
* If the command prompt appeared for a moment and then closed, then you are probably running `login.py` with Python 3. Consider installing Python 2, or if you have already installed it, right-click `login.py` and open it with Python 2 using the "Open With..." option.
* If the command prompt closed after taking user input, then an unexpected error occured during the login process. Try running it again in `cmd.exe` in order to see what happened, and if it looks like a problem, please [open an issue](https://github.com/relrelb/CPPS-PCL/issues/new) regarding it.

### Can I add all items?
Sure, you can accomplish that by writing a custom script using the [API](#api). An example can be found in the answer at [Issue #3](https://github.com/relrelb/CPPS-PCL/issues/3#issuecomment-345218486).

### Can I login to a CPPS that is not listed above?
Absolutely, you can add more CPPSs yourself by editing [`json/servers.json`](https://github.com/relrelb/CPPS-PCL/blob/master/json/servers.json).

### Can I add more shapes to Multi-Login?
Of course, you can define more shapes by editing [`json/shapes.json`](https://github.com/relrelb/CPPS-PCL/blob/master/json/shapes.json).

### Is autocompletion also available in Windows?
Yes, in order to get that you need [PyReadline](https://pypi.org/project/pyreadline/) (can be installed with:  `pip install pyreadline`).
