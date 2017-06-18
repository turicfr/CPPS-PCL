# CPPS-PCL
A simple Penguin Client Library for Club Penguin Private Servers written in Python

# Requirements
- Python 2.x or 3.x
- Internet connection
- Computer

# Usage
1. Run login.py
2. Enter your username and password
3. Choose a server
4. Waddle on!

# Commands
- help - prints "HELP" (will be done in the future)
- walk [x] [y] - walks to ([x], [y])
- say [message] - says [message]
- joke [id] - says joke with id [id]
- room [id] - goes to room with id [id]
- item [id] - adds items with id [id]
- follow [name] - follows a penguin named [name]
- unfollow - disables follow
- logout - logouts

# Tips and Tricks
- Edit json/servers.json in order to define more CPPSs and servers (ports can be found using a packet sniffer)
- Turn on log by changing line 67 in login.py to 'client = client.Client(ip, login, port, True)'
