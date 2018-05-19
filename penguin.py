class Penguin(object):
	def __init__(self, penguin_id, name, member, color, head, face, neck, body, hand, feet, pin, background, x=None, y=None, frame=None, unknown=None, rank=None):
		self.id = penguin_id
		self.name = name
		self.member = member
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
		self.frame = frame
		# self.??? = unknown
		self.rank = rank
		self.online = None

	@classmethod
	def from_player(cls, player):
		if not player:
			raise ValueError("Invalid player")
		player = player.split("|")
		penguin_id = int(player[0])
		name = player[1]
		member = int(player[2])
		color = int(player[3], 0)
		head = int(player[4])
		face = int(player[5])
		neck = int(player[6])
		body = int(player[7])
		hand = int(player[8])
		feet = int(player[9])
		pin = int(player[10])
		background = int(player[11])
		if len(player) > 16:
			x = int(player[12])
			y = int(player[13])
			frame = int(player[14])
			unknown = int(player[15])
			rank = int(player[16])
			return cls(penguin_id, name, member, color, head, face, neck, body, hand, feet, pin, background, x, y, frame, unknown, rank)
		if len(player) > 12:
			# ??? = int(player[12])
			return cls(penguin_id, name, member, color, head, face, neck, body, hand, feet, pin, background)
		return cls(penguin_id, name, member, color, head, face, neck, body, hand, feet, pin, background)

	@classmethod
	def from_buddy(cls, buddy):
		if not buddy:
			raise ValueError("Invalid buddy")
		penguin_id, name, online = buddy.split("|")
		penguin = cls(int(penguin_id), name, None, None, None, None, None, None, None, None, None, None)
		penguin.online = online == "1"
		return penguin
