import struct
import time

from . import zandronum
from . import enums
from . import huffman
from . import asyncudp
from .player import Player


class AsyncServer(zandronum.Server):
    def __init__(
        self,
        address: str,
        port: int = 10666,
        flags: enums.RequestFlags = enums.RequestFlags.default()
    ) -> None:
        self.address: str = address
        self.port: int = port
        self.response: int = None
        self.response_time: int = None
        self.response_flags: int = None
        self.query_dict = {
            'version': None,
            'hostname': None,
            'url': None,
            'map': None,
            'maxclients': None,
            'maxplayers': None,
            'pwads_loaded': None,
            'pwads_list': None,
            'gamemode': None,
            'teamgame': None,
            'instagib': None,
            'buckshot': None,
            'gamename': None,
            'iwad': None,
            'forcepassword': None,
            'forcejoinpassword': None,
            'skill': None,
            'botskill': None,
            'fraglimit': None,
            'timelimit': None,
            'timelimit_left': None,
            'duellimit': None,
            'pointlimit': None,
            'winlimit': None,
            'numplayers': None
        }
        self.players: list[Player] = []

        self._huffman = huffman.Huffman(huffman.HUFFMAN_FREQS)
        self._sock: asyncudp.Socket = None
        self._request_flags: int = flags.value
        self._buffsize: int = 8192
        self._bytepos: int = 0
        self._raw_data: bytes = b''

    async def __aenter__(self) -> "AsyncServer":
        await self.query()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        pass

    async def query(self):
        """
        Asynchronous requests server query to fetch server infomation.
        """
        # Launcher challenge
        request = struct.pack('l', 199)
        # Desired information
        request += struct.pack('l', self._request_flags)
        # Current time, this will be sent back to you so you can determine ping
        request += struct.pack('l', int(time.time()))

        # Compress query request with the Huffman algorithm
        request_encoded = self._huffman.encode(request)

        # Send the query request to Zandronum server
        self._sock = await asyncudp.create_socket(
            remote_addr=(self.address, self.port)
        )
        self._sock.sendto(request_encoded)
        data, server = await self._sock.recvfrom()
        self._raw_data = self._huffman.decode(data)
        self._sock.close()

        # Calling method for parsing server query response
        self._parse()
