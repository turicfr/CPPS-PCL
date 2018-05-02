import client

class Penguin:
	def __init__(self, penguin_id, name, frame, color, head, face, neck, body, hand, feet, pin, background, x=None, y=None):
		self._id = penguin_id
		self._name = name
		self._frame = frame
		self._color = color
		self._head = head
		self._face = face
		self._neck = neck
		self._body = body
		self._hand = hand
		self._feet = feet
		self._pin = pin
		self._background = background
		self._x = x
		self._y = y

	@classmethod
	def from_player(cls, player):
		if not player:
			raise client.ClientError("Invalid player")
		player = player.split("|")
		penguin_id = int(player[0])
		name = player[1]
		frame = player[2]
		color = int(player[3], 0)
		head = int(player[4])
		face = int(player[5])
		neck = int(player[6])
		body = int(player[7])
		hand = int(player[8])
		feet = int(player[9])
		pin = int(player[10])
		background = int(player[11])
		if len(player) > 12:
			x = int(player[12])
			y = int(player[13])
			return cls(penguin_id, name, frame, color, head, face, neck, body, hand, feet, pin, background, x, y)
		return cls(penguin_id, name, frame, color, head, face, neck, body, hand, feet, pin, background)

	@property
	def id(self):
		return self._id

	@property
	def name(self):
		return self._name

	@property
	def frame(self):
		return self._frame

	@property
	def color(self):
		return self._color

	@property
	def head(self):
		return self._head

	@property
	def face(self):
		return self._face

	@property
	def neck(self):
		return self._neck

	@property
	def body(self):
		return self._body

	@property
	def hand(self):
		return self._hand

	@property
	def feet(self):
		return self._feet

	@property
	def pin(self):
		return self._pin

	@property
	def background(self):
		return self._background

	@property
	def x(self):
		return self._x

	@property
	def y(self):
		return self._y
