class Penguin:
	def __init__(self, id, name, frame, color, head, face, neck, body, hand, feet, pin, background, x, y):
		self.id = id
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
		player = player.split('|')
		id = int(player[0])
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
		x = int(player[12])
		y = int(player[13])
		return cls(id, name, frame, color, head, face, neck, body, hand, feet, pin, background, x, y)
