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
        self.response = None
        self.response_flags = None
        self.flags = None
        self.time = None

        self.sock.settimeout(timeout)

        self._bytepos = 0
        self._raw_data = b''
        self._query_dict = {
            'version': None,
            'hostname': None,
            'url': None,
            'map': None,
            'maxclients': None,
            'maxplayers': None,
            'pwads_loaded': None,
            'pwads_list': None,
            'gamemode': None,
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
        self._query_dict['gamemode'] = enums.Gamemode(self._next_bytes(1))
        # Instagib
        if self._next_bytes(1) == 1:
            self._query_dict['instagib'] = True
        else:
            self._query_dict['instagib'] = False
        # Buckshot
        if self._next_bytes(1) == 1:
            self._query_dict['buckshot'] = True
        else:
            self._query_dict['buckshot'] = False
        # The game's name ("DOOM", "DOOM II", "HERETIC", "HEXEN", "ERROR!")
        self._query_dict['gamename'] = self._next_string()
        # The IWAD's name
        self._query_dict['iwad'] = self._next_string()
        # Whether a password is required to join the server
        if self._next_bytes(1) == 1:
            self._query_dict['forcepassword'] = True
        else:
            self._query_dict['forcepassword'] = False
        # Whether a password is required to join the game
        if self._next_bytes(1) == 1:
            self._query_dict['forcejoinpassword'] = True
        else:
            self._query_dict['forcejoinpassword'] = False
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

    @property
    def version(self) -> str:
        """:class:`str`: Returns the host's version."""
        return self._query_dict['version']

    @property
    def name(self) -> str:
        """:class:`str`: Returns the host's name."""
        return self._query_dict['hostname']

    @property
    def url(self) -> str:
        """:class:`str`: Returns the host's URL website.
        Uses for downloading PWADs from self-hosted."""
        return self._query_dict['url']

    @property
    def map(self) -> str:
        """:class:`str`: Returns the host's current game map."""
        return self._query_dict['map']

    @property
    def max_clients(self) -> int:
        """:class:`int`: Returns the host's maximum clients in host."""
        return self._query_dict['maxclients']

    @property
    def max_players(self) -> int:
        """:class:`int`: Returns the host's maximum players in game."""
        return self._query_dict['maxplayers']

    @property
    def pwads_loaded(self) -> int:
        """:class:`int`: Returns the count of loaded PWADs in host."""
        return self._query_dict['pwads_loaded']

    @property
    def pwads(self) -> list:
        """:class:`list`: Returns the list of loaded PWADs in host."""
        return self._query_dict['pwads_list']

    @property
    def gamemode(self) -> enums.Gamemode:
        """:class:`Gamemode`: Returns the host's current game mode."""
        return self._query_dict['gamemode']

    @property
    def instagib(self) -> bool:
        """:class:`bool`: Returns True if Instagib modifier
        is enabled on the host."""
        return self._query_dict['instagib']

    @property
    def buckshot(self) -> bool:
        """:class:`bool`: Returns True if Buckshot modifier
        is enabled on the host."""
        return self._query_dict['buckshot']

    @property
    def gamename(self) -> str:
        """:class:`str`: Returns host's game name from IWAD."""
        return self._query_dict['gamename']

    @property
    def iwad(self) -> str:
        """:class:`str`: Returns host's current IWAD filename."""
        return self._query_dict['iwad']

    @property
    def force_password(self) -> bool:
        """:class:`bool`: Returns True if host forces password
        for connection."""
        return self._query_dict['forcepassword']

    @property
    def force_join_password(self) -> bool:
        """:class:`bool`: Returns True if host forces password
        for joining the game."""
        return self._query_dict['forcejoinpassword']

    @property
    def skill(self) -> int:
        """:class:`int`: Returns the host's game skill."""
        return self._query_dict['skill']

    @property
    def bot_skill(self) -> int:
        """:class:`int`: Returns the host's bot skill."""
        return self._query_dict['botskill']

    @property
    def frag_limit(self) -> int:
        """:class:`int`: Returns the game's frag limit."""
        return self._query_dict['fraglimit']

    @property
    def time_limit(self) -> int:
        """:class:`int`: Returns the game's time limit."""
        return self._query_dict['timelimit']

    @property
    def time_limit_left(self) -> int:
        """:class:`int`: Returns the game's time limit left in minutes."""
        return self._query_dict['timelimit_left']

    @property
    def duel_limit(self) -> int:
        """:class:`int`: Returns the game's duels limit."""
        return self._query_dict['duellimit']

    @property
    def point_limit(self) -> int:
        """:class:`int`: Returns the game's points limit in CTF."""
        return self._query_dict['pointlimit']

    @property
    def win_limit(self) -> int:
        """:class:`int`: Returns the game's win count limit."""
        return self._query_dict['winlimit']

    @property
    def number_players(self) -> int:
        """:class:`int`: Returns the host's number of players in game."""
        return self._query_dict['numplayers']

    @property
    def email(self) -> str:
        """:class:`str`: Returns the host's E-Mail address."""
        return self._query_dict['hostemail']

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
