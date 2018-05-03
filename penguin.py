class Penguin(object):
	def __init__(self, penguin_id, name, frame, color, head, face, neck, body, hand, feet, pin, background, x=None, y=None):
		self.id = penguin_id
		self.name = name
		self.frame = frame
		self.color = color
		self.head = head
		self.face = face
		self.neck = neck
		self.body = body
		self.hand = hand
		self.feet = feet
		self.pin = pin
		self.background = background
		self.x = x
		self.y = y

	@classmethod
	def from_player(cls, player):
		if not player:
			raise ValueError("Invalid player")
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
