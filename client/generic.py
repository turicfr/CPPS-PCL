import re
import socket
import hashlib
import functools

from .xt import parser as xt
from .client import Client

BUFFER_SIZE = 4096

PACKET_HANDLERS = {}

def swapped_md5(password):
    digest = hashlib.md5(password.encode("ascii")).hexdigest()
    return digest[16:32] + digest[0:16]

class GenericClient(Client):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.buffer = b""
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
        self._send(request)

        self.update()
        self.socket.setblocking(False)

    def update(self):
        try:
            data = self._recv()
        except BlockingIOError:
            return
        packet = xt.parse(data)
        self.handle_packet(packet)

    def handle_packet(self, packet):
        if packet[2] not in PACKET_HANDLERS:
            print(f"Unhandled packet: {'%'.join(packet)}")
            return
        PACKET_HANDLERS[packet[2]](self, packet)

    @property
    def id(self):
        return self._id

    def packet_handler(name):
        def _packet_handler(func):
            @functools.wraps(func)
            def _func(self, packet):
                func(self, packet)
            PACKET_HANDLERS[name] = _func
            return _func
        return _packet_handler

    @packet_handler("l")
    def handle_login(self, packet):
        data = packet[4].split("|")
        self._id = int(data[0])
