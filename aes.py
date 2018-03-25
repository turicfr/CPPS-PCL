import random
import binascii

class AES():
	rcon = [1, 2, 4, 8, 16, 32, 64, 128, 27, 54, 108, 216, 171, 77, 154, 47, 94, 188, 99, 198, 151, 53, 106, 212, 179, 125, 250, 239, 197, 145]
	sbox = [99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118, 202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192, 183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21, 4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117, 9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132, 83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207, 208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168, 81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210, 205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115, 96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219, 224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121, 231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8, 186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138, 112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158, 225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223, 140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22]
	sbox_inverse = [82, 9, 106, 213, 48, 54, 165, 56, 191, 64, 163, 158, 129, 243, 215, 251, 124, 227, 57, 130, 155, 47, 255, 135, 52, 142, 67, 68, 196, 222, 233, 203, 84, 123, 148, 50, 166, 194, 35, 61, 238, 76, 149, 11, 66, 250, 195, 78, 8, 46, 161, 102, 40, 217, 36, 178, 118, 91, 162, 73, 109, 139, 209, 37, 114, 248, 246, 100, 134, 104, 152, 22, 212, 164, 92, 204, 93, 101, 182, 146, 108, 112, 72, 80, 253, 237, 185, 218, 94, 21, 70, 87, 167, 141, 157, 132, 144, 216, 171, 0, 140, 188, 211, 10, 247, 228, 88, 5, 184, 179, 69, 6, 208, 44, 30, 143, 202, 63, 15, 2, 193, 175, 189, 3, 1, 19, 138, 107, 58, 145, 17, 65, 79, 103, 220, 234, 151, 242, 207, 206, 240, 180, 230, 115, 150, 172, 116, 34, 231, 173, 53, 133, 226, 249, 55, 232, 28, 117, 223, 110, 71, 241, 26, 113, 29, 41, 197, 137, 111, 183, 98, 14, 170, 24, 190, 27, 252, 86, 62, 75, 198, 210, 121, 32, 154, 219, 192, 254, 120, 205, 90, 244, 31, 221, 168, 51, 136, 7, 199, 49, 177, 18, 16, 89, 39, 128, 236, 95, 96, 81, 127, 169, 25, 181, 74, 13, 45, 229, 122, 159, 147, 201, 156, 239, 160, 224, 59, 77, 174, 42, 245, 176, 200, 235, 187, 60, 131, 83, 153, 97, 23, 43, 4, 126, 186, 119, 214, 38, 225, 105, 20, 99, 85, 33, 12, 125]
	key_size = 128
	block_size = 128

	def __init__(self, key_size, block_size):
		if key_size is not None:
			self.key_size = key_size
		if block_size is not None:
			self.block_size = block_size
		self.rounds_array = [0, 0, 0, 0, [0, 0, 0, 0, 10, 0, 12, 0, 14], 0, [0, 0, 0, 0, 12, 0, 12, 0, 14], 0, [0, 0, 0, 0, 14, 0, 14, 0, 14]]
		self.shift_offsets = [0, 0, 0, 0, [0, 1, 2, 3], 0, [0, 1, 2, 3], 0, [0, 1, 3, 4]]
		self.nb = block_size / 32
		self.nk = key_size / 32
		self.nr = self.rounds_array[self.nk][self.nb]

	def encrypt(self, src, key, mode):
		result = []
		block = []
		block_size = self.block_size / 8
		if mode == "CBC":
			result = self.get_random_bytes(block_size)
		formatted_plaintext = self.format_plaintext(self.str_to_chars(src))
		expanded_key = self.key_expansion(self.str_to_chars(key))
		for i in range(len(formatted_plaintext) / block_size):
			block = formatted_plaintext[i * block_size:(i + 1) * block_size]
			if mode == "CBC":
				for j in range(block_size):
					block[j] = block[j] ^ result[i * block_size + j]
			result += self.encryption(block, expanded_key)
		return self.chars_to_hex(result)

	def decrypt(self, src, key, mode):
		result = []
		block = []
		chars = self.hex_to_chars(src)
		block_size = self.block_size / 8
		expanded_key = self.key_expansion(self.str_to_chars(key))
		for i in range(len(chars) / block_size - 1, 0, -1):
			block = self.decryption(chars[i * block_size:(i + 1) * block_size], expanded_key)
			if mode == "CBC":
				for j in range(block_size):
					result[(i - 1) * block_size + j] = block[j] ^ chars[(i - 1) * block_size + j]
			else:
				result = block + result
		if mode == "ECB":
			result = self.decryption(chars[:block_size], expanded_key) + result
		return self.chars_to_str(result)

	def cyclic_shift_left(self, src, pos):
		return src[pos:] + src[:pos]

	def xtime(self, poly):
		poly <<= 1
		return poly ^ 0x11B if (poly & 0x100) else poly

	def mult_gf256(self, x, y):
		result = 0
		bit = 1
		while bit < 0x100:
			if x & bit:
				result ^= y
			bit <<= 1
			y = self.xtime(y)
		return result

	def byte_sub(self, state, dir):
		sbox = self.sbox if dir == "encrypt" else self.sbox_inverse
		for i in range(4):
			for j in range(self.nb):
				state[i][j] = sbox[state[i][j]]

	def shift_row(self, state, dir):
		for i in range(1, 4):
			if dir == "encrypt":
				state[i] = self.cyclic_shift_left(state[i], self.shift_offsets[self.nb][i])
			else:
				state[i] = self.cyclic_shift_left(state[i], self.nb - self.shift_offsets[self.nb][i])

	def mix_column(self, state, dir):
		column = [0] * 4
		for i in range(self.nb):
			for j in range(4):
				if dir == "encrypt":
					column[j] = self.mult_gf256(state[j][i], 2) ^ self.mult_gf256(state[(j + 1) % 4][i], 3) ^ state[(j + 2) % 4][i] ^ state[(j + 3) % 4][i]
				else:
					column[j] = self.mult_gf256(state[j][i], 14) ^ self.mult_gf256(state[(j + 1) % 4][i], 11) ^ self.mult_gf256(state[(j + 2) % 4][i], 13) ^ self.mult_gf256(state[(j + 3) % 4][i], 9)
			for j in range(4):
				state[j][i] = column[j]

	def add_round_key(self, state, round_key):
		for i in range(self.nb):
			state[0][i] ^= round_key[i] & 0xFF
			state[1][i] ^= round_key[i] >> 8 & 0xFF
			state[2][i] ^= round_key[i] >> 16 & 0xFF
			state[3][i] ^= round_key[i] >> 24 & 0xFF

	def key_expansion(self, key):
		byte = 0
		self.nk = self.key_size / 32
		self.nb = self.block_size / 32
		result = []
		self.nr = self.rounds_array[self.nk][self.nb]
		for i in range(self.nk):
			result.append(key[4 * i] | key[4 * i + 1] << 8 | key[4 * i + 2] << 16 | key[4 * i + 3] << 24)
		for i in range(self.nk, self.nb * (self.nr + 1)):
			byte = result[i - 1]
			if i % self.nk == 0:
				byte = (self.sbox[byte >> 8 & 0xFF] | self.sbox[byte >> 16 & 0xFF] << 8 | self.sbox[byte >> 24 & 0xFF] << 16 | self.sbox[byte & 0xFF] << 24) ^ self.rcon[i / self.nk - 1]
			elif self.nk > 6 and i % self.nk == 4:
				byte = self.sbox[byte >> 24 & 0xFF] << 24 | self.sbox[byte >> 16 & 0xFF] << 16 | self.sbox[byte >> 8 & 0xFF] << 8 | self.sbox[byte & 0xFF]
			result.append(result[i - self.nk] ^ byte)
		return result

	def round(self, state, round_key):
		self.byte_sub(state, "encrypt")
		self.shift_row(state, "encrypt")
		self.mix_column(state, "encrypt")
		self.add_round_key(state, round_key)

	def inverse_round(self, state, round_key):
		self.add_round_key(state, round_key)
		self.mix_column(state, "decrypt")
		self.shift_row(state, "decrypt")
		self.byte_sub(state, "decrypt")

	def final_round(self, state, round_key):
		self.byte_sub(state, "encrypt")
		self.shift_row(state, "encrypt")
		self.add_round_key(state, round_key)

	def inverse_final_round(self, state, round_key):
		self.add_round_key(state, round_key)
		self.shift_row(state, "decrypt")
		self.byte_sub(state, "decrypt")

	def encryption(self, block, expanded_key):
		block = self.pack_bytes(block)
		self.add_round_key(block, expanded_key)
		for i in range(1, self.nr):
			self.round(block, expanded_key[self.nb * i:self.nb * (i + 1)])
		self.final_round(block, expanded_key[self.nb * self.nr:])
		return self.unpack_bytes(block)

	def decryption(self, block, expanded_key):
		block = self.pack_bytes(block)
		self.inverse_final_round(block, expanded_key[self.nb * self.nr:])
		for i in range(self.nr - 1, 0, -1):
			self.inverse_round(block, expanded_key[self.nb * i:self.nb * (i + 1)])
		self.add_round_key(block, expanded_key)
		return self.unpack_bytes(block)

	def pack_bytes(self, octects):
		return [octects[i:len(octects):4] for i in range(4)]

	def unpack_bytes(self, packed):
		return [packed[i % 4][i / 4] for i in range(sum(len(i) for i in packed))]

	def format_plaintext(self, plaintext):
		block_size = self.block_size / 8
		if len(plaintext) % block_size == 0:
			return plaintext
		return plaintext + [0] * (block_size - len(plaintext) % block_size)

	def get_random_bytes(self, count):
		return [random.randint(0, 0x100) for i in range(count)]

	def hex_to_chars(self, hex):
		return self.str_to_chars(binascii.unhexlify(hex))

	def chars_to_hex(self, chars):
		return binascii.hexlify(self.chars_to_str(chars))

	def chars_to_str(self, chars):
		return "".join(chr(char) for char in chars)

	def str_to_chars(self, string):
		return [ord(char) for char in string]
