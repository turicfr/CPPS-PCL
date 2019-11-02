import re
import socket
import select
import hashlib

from .xt import xt
from .client import Client

BUFFER_SIZE = 4096

def swapped_md5(password):
    digest = hashlib.md5(password.encode("ascii")).hexdigest()
    return digest[16:32] + digest[0:16]

class GenericClient(Client):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.buffer = b""
        self.handlers = {}
        self._id = None

    def _send(self, data):
        print(f"-> {data}")
        self.socket.sendall(data.encode("ascii") + b"\0")

    def _recv(self):
        chunk = self.buffer
        self.buffer = b""
        while (index := chunk.find(b"\0")) < 0:
            self.buffer += chunk
            chunk = self.socket.recv(BUFFER_SIZE)
        data = (self.buffer + chunk[:index]).decode("ascii")
        self.buffer = chunk[index + 1:]
        print(f"<- {data}")
        return data

    def _send_recv(self, data):
        self._send(data)
        return self._recv()

    @property
    def magic(self):
        return "Y(02.>'H}t\":E1"

    def login(self, username, password):
        print("Connecting...")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.port))
        except OSError as e:
            print(f"Error: {e}")
        print("Connected!")

        request = f'<msg t="sys"><body action="verChk" r="0"><ver v="{153}" /></body></msg>'
        response = self._send_recv(request)

        request = f'<msg t="sys"><body action="rndK" r="-1"></body></msg>'
        response = self._send_recv(request)
        rndk = re.search(r"<k>(?:<!\[CDATA\[)?(?P<rndk>.*?)(?:\]\]>)?<\/k>", response).group("rndk")
        print(f"{rndk=}")

        pword = swapped_md5(swapped_md5(password).upper() + rndk + self.magic)
        request = f'<msg t="sys"><body action="login" r="0"><login z="w1"><nick><![CDATA[{username}]]></nick><pword><![CDATA[{pword}]]></pword></login></body></msg>'
        response = self._send(request)

    def update(self):
        select.select([self.socket], [], [], 0)
        # self.handlers["l"] = self.handle_login
        # while True:
        #     packet = xt.parse(self._recv())
        #     if packet[2] not in self.handlers:
        #         print(f"Unhandled packet: {'%'.join(packet)}")
        #         continue
        #     self.handlers[packet[2]](packet)

    def handle_login(self, packet):
        data = packet[4].split("|")
        self._id = int(data[0])

    @property
    def id(self):
        assert self._id is not None
        return self._id
