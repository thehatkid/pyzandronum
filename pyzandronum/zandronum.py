import struct
import socket
import time

from . import enums
from . import huffman
from . import exceptions


class Server:
    """
    Represents a Zandronum server.
    """

    def __init__(
        self,
        address: str,
        port: int = 10666,
        flags: enums.RequestFlags = enums.RequestFlags.default(),
        timeout: float = 5.0
    ) -> None:
        self.address = address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.request_flags = flags.value
        self.huffman = huffman.Huffman(huffman.HUFFMAN_FREQS)
        self.flags = 0

        self._bytepos = 0
        self._raw_data = None
        self._response = None
        self._time = None
        self._flags = None
        self._query_dict = {}

        self.sock.settimeout(timeout)

    def query(self) -> None:
        """
        Requests server query to fetch server infomation.
        """
        # Our request packet is 3 32-bit integers in a row, for a total of
        # 12 bytes (32 bit = 4 bytes). They must be converted to the "byte"
        # type, with appropriate length and encoded little-endian.
        # The numbers are: 199 + bitwise OR hex flags + epoch timestamp
        # (concatenated, not added).

        # Launcher challenge
        request = struct.pack('l', 199)
        # Desired information
        request += struct.pack('l', self.request_flags)
        # Current time, this will be sent back to you so you can determine ping
        request += struct.pack('l', int(time.time()))

        # Compress query request with the Huffman algorithm
        request_encoded = self.huffman.encode(request)

        # Send the query request to Zandronum server
        self.sock.sendto(request_encoded, (self.address, self.port))
        data, server = self.sock.recvfrom(8192)
        self._raw_data = self.huffman.decode(data)

        # Calling method for parsing server query response
        self._parse()

    def _parse(self) -> None:
        """
        Parsing server raw infomation data to properties.
        """

        # We start at position 0, beginning of our raw data stream
        self._bytepos = 0

        # 0: Get server response header and time stamp (both 4 byte long ints)
        # Server response
        self._response = self._next_bytes(4)
        # Time which you sent to the server
        self._time = self._next_bytes(4)

        # Checking server response magic number
        if self._response != enums.Response.ACCEPTED.value:
            if self._response == enums.Response.DENIED_QUERY.value:
                raise exceptions.QueryIgnored
            elif self._response == enums.Response.DENIED_BANNED.value:
                raise exceptions.QueryBanned
            else:
                raise exceptions.QueryDenied

        # 1: String of Zandronum server version
        self._query_dict['version'] = self._next_string()

        # 2: Our flags are repeated back to us (long int)
        self._flags = self._next_bytes(4)

        # 3: Flags
        # The server's name (sv_hostname)
        self._query_dict['hostname'] = self._next_string()
        # The server's WAD URL (sv_website)
        self._query_dict['url'] = self._next_string()
        # The server host's e-mail (sv_hostemail)
        self._query_dict['hostemail'] = self._next_string()
        # The current map's name
        self._query_dict['map'] = self._next_string()
        # The max number of clients (sv_maxclients)
        self._query_dict['maxclients'] = self._next_bytes(1)
        # The max number of players (sv_maxplayers)
        self._query_dict['maxplayers'] = self._next_bytes(1)
        # The number of PWADs loaded
        self._query_dict['pwads_loaded'] = self._next_bytes(1)
        # The PWAD's name (sent for each PWAD)
        self._query_dict['pwads_list'] = []
        if int(self._query_dict['pwads_loaded']) > 0:
            for i in range(0, self._query_dict['pwads_loaded']):
                self._query_dict['pwads_list'].append(self._next_string())
        # The current gamemode
        self._query_dict['gamemode'] = self._next_bytes(1)
        # Instagib
        self._query_dict['instagib'] = self._next_bytes(1)
        # Buckshot
        self._query_dict['instagib'] = self._next_bytes(1)
        # The game's name ("DOOM", "DOOM II", "HERETIC", "HEXEN", "ERROR!")
        self._query_dict['gamename'] = self._next_string()
        # The IWAD's name
        self._query_dict['iwad'] = self._next_string()
        # Whether a password is required to join the server
        self._query_dict['forcepassword'] = self._next_bytes(1)
        # Whether a password is required to join the game
        self._query_dict['forcejoinpassword'] = self._next_bytes(1)
        # The game's difficulty (skill)
        self._query_dict['skill'] = self._next_bytes(1)
        # The bot difficulty (botskill)
        self._query_dict['botskill'] = self._next_bytes(1)
        # Value of fraglimit
        self._query_dict['fraglimit'] = self._next_bytes(2)
        # Value of timelimit
        self._query_dict['timelimit'] = self._next_bytes(2)
        # Time left in minutes (only sent if timelimit > 0)
        self._query_dict['timelimit_left'] = 0
        if self._query_dict['timelimit'] != 0:
            self._query_dict['timelimit_left'] = self._next_bytes(2)
        # Duel limit (duellimit)
        self._query_dict['duellimit'] = self._next_bytes(2)
        # Point limit (pointlimit)
        self._query_dict['pointlimit'] = self._next_bytes(2)
        # Win limit (winlimit)
        self._query_dict['winlimit'] = self._next_bytes(2)
        # The number of players in the server
        self._query_dict['numplayers'] = self._next_bytes(1)
        # TODO: append some flags from query

    def _next_bytes(self, bytes_length: int):
        ret_int = int.from_bytes(
            self._raw_data[self._bytepos:self._bytepos + bytes_length],
            byteorder='little', signed=False
        )
        self._bytepos += bytes_length
        return ret_int

    def _next_string(self) -> str:
        ret_str = ''

        # Read characters until we hit a null, and add them to our string
        while int(self._raw_data[self._bytepos]) != 0:
            ret_str = ret_str + chr(int(self._raw_data[self._bytepos]))
            self._bytepos += 1

        # Advance our byte counter 1 more, to get past our null byte:
        self._bytepos += 1

        return ret_str
