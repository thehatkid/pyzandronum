import struct
import socket
import time

from . import enums
from . import huffman
from . import exceptions
from .player import Player


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
        self.address: str = address
        self.port: int = port
        self.response: int = None
        self.response_time: int = None
        self.response_flags: int = None
        self.query_dict = {
            'version': None,
            'hostname': None,
            'url': None,
            'hostemail': None,
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
            'numplayers': None,
            'testing_server': None,
            'testing_server_archive': None,
            'dmflags_number': None,
            'dmflags': None,
            'dmflags2': None,
            'zadmflags': None,
            'compatflags': None,
            'zacompatflags': None,
            'compatflags2': None,
            'security_settings': None,
            'optional_pwads_count': None,
            'optional_pwads': None,
            'deh_loaded': None,
            'deh_list': None
        }
        self.players: list[Player] = []

        self._huffman = huffman.Huffman(huffman.HUFFMAN_FREQS)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._request_flags = flags.value
        self._buffsize = 8192
        self._bytepos = 0
        self._raw_data = b''

        self._sock.settimeout(timeout)

    def __enter__(self) -> "Server":
        self.query()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._sock.close()

    def query(self) -> "Server":
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
        request += struct.pack('l', self._request_flags)
        # Current time, this will be sent back to you so you can determine ping
        request += struct.pack('l', int(time.time()))

        # Compress query request with the Huffman algorithm
        request_encoded = self._huffman.encode(request)

        # Send the query request to Zandronum server
        self._sock.sendto(request_encoded, (self.address, self.port))
        data, server = self._sock.recvfrom(self._buffsize)
        self._raw_data = self._huffman.decode(data)

        # Calling method for parsing server query response
        self._parse()

        return self

    def _parse(self) -> None:
        """
        Parsing server raw infomation data to properties.
        """

        # We start at position 0, beginning of our raw data stream
        self._bytepos = 0

        # 0: Get server response header and time stamp (both 4 byte long ints)
        # Server response
        self.response = self._next_bytes(4)
        # Time which you sent to the server
        self.response_time = self._next_bytes(4)

        # Checking server response magic number
        if self.response != enums.Response.ACCEPTED.value:
            if self.response == enums.Response.DENIED_QUERY.value:
                raise exceptions.QueryIgnored
            elif self.response == enums.Response.DENIED_BANNED.value:
                raise exceptions.QueryBanned
            else:
                raise exceptions.QueryDenied

        # 1: String of Zandronum server version
        self.query_dict['version'] = self._next_string()

        # 2: Our flags are repeated back to us (long int)
        self.response_flags = self._next_bytes(4)

        # 3: Flags
        # The server's name (sv_hostname)
        self.query_dict['hostname'] = self._next_string()
        # The server's WAD URL (sv_website)
        self.query_dict['url'] = self._next_string()
        # The server host's e-mail (sv_hostemail)
        self.query_dict['hostemail'] = self._next_string()
        # The current map's name
        self.query_dict['map'] = self._next_string()
        # The max number of clients (sv_maxclients)
        self.query_dict['maxclients'] = self._next_bytes(1)
        # The max number of players (sv_maxplayers)
        self.query_dict['maxplayers'] = self._next_bytes(1)
        # The number of PWADs loaded
        self.query_dict['pwads_loaded'] = self._next_bytes(1)
        # The PWAD's name (sent for each PWAD)
        self.query_dict['pwads_list'] = []
        if int(self.query_dict['pwads_loaded']) > 0:
            for i in range(0, self.query_dict['pwads_loaded']):
                self.query_dict['pwads_list'].append(self._next_string())
        # The current gamemode
        self.query_dict['gamemode'] = enums.Gamemode(self._next_bytes(1))
        # Sets teamgame boolean if gamemode with teams
        if self.query_dict['gamemode'] in [
            enums.Gamemode.TEAMPLAY,
            enums.Gamemode.TEAMLMS,
            enums.Gamemode.TEAMPOSSESSION
        ]:
            self.query_dict['teamgame'] = True
        else:
            self.query_dict['teamgame'] = False
        # Instagib
        if self._next_bytes(1) == 1:
            self.query_dict['instagib'] = True
        else:
            self.query_dict['instagib'] = False
        # Buckshot
        if self._next_bytes(1) == 1:
            self.query_dict['buckshot'] = True
        else:
            self.query_dict['buckshot'] = False
        # The game's name ("DOOM", "DOOM II", "HERETIC", "HEXEN", "ERROR!")
        self.query_dict['gamename'] = self._next_string()
        # The IWAD's name
        self.query_dict['iwad'] = self._next_string()
        # Whether a password is required to join the server
        if self._next_bytes(1) == 1:
            self.query_dict['forcepassword'] = True
        else:
            self.query_dict['forcepassword'] = False
        # Whether a password is required to join the game
        if self._next_bytes(1) == 1:
            self.query_dict['forcejoinpassword'] = True
        else:
            self.query_dict['forcejoinpassword'] = False
        # The game's difficulty (skill)
        self.query_dict['skill'] = self._next_bytes(1)
        # The bot difficulty (botskill)
        self.query_dict['botskill'] = self._next_bytes(1)
        # Value of fraglimit
        self.query_dict['fraglimit'] = self._next_bytes(2)
        # Value of timelimit
        self.query_dict['timelimit'] = self._next_bytes(2)
        # Time left in minutes (only sent if timelimit > 0)
        self.query_dict['timelimit_left'] = 0
        if self.query_dict['timelimit'] != 0:
            self.query_dict['timelimit_left'] = self._next_bytes(2)
        # Duel limit (duellimit)
        self.query_dict['duellimit'] = self._next_bytes(2)
        # Point limit (pointlimit)
        self.query_dict['pointlimit'] = self._next_bytes(2)
        # Win limit (winlimit)
        self.query_dict['winlimit'] = self._next_bytes(2)
        # The number of players in the server
        self.query_dict['numplayers'] = self._next_bytes(1)
        # Player datas
        if self.query_dict['numplayers'] > 0:
            for i in range(0, int(self.query_dict['numplayers'])):
                self.players.append(Player(
                    self._raw_data,
                    self._bytepos,
                    self.query_dict['teamgame']
                ))
                self._bytepos = self.players[i]._bytepos
        # Whether this server is running a testing binary
        if self._next_bytes(1):
            self.query_dict['testing_server'] = True
        else:
            self.query_dict['testing_server'] = False
        # An empty string in case the server is running a stable binary,
        # otherwise name of the testing binary
        self.query_dict['testing_server_archive'] = self._next_string()
        # The number of flags that will be sent
        self.query_dict['dmflags_number'] = self._next_bytes(1)
        # The values of the flags (SQF_ALL_DMFLAGS)
        self.query_dict['dmflags'] = self._next_bytes(4)
        self.query_dict['dmflags2'] = self._next_bytes(4)
        self.query_dict['zadmflags'] = self._next_bytes(4)
        self.query_dict['compatflags'] = self._next_bytes(4)
        self.query_dict['zacompatflags'] = self._next_bytes(4)
        self.query_dict['compatflags2'] = self._next_bytes(4)
        # Whether the server is enforcing the master ban list. (boolean)
        # The other bits of this byte may be used to transfer other
        # security related settings in the future.
        self.query_dict['security_settings'] = self._next_bytes(1)
        # Amount of optional wad indices that follow
        self.query_dict['optional_pwads_count'] = self._next_bytes(1)
        # The optional PWAD's name (sent for each PWAD)
        self.query_dict['optional_pwads'] = []
        if self.query_dict['optional_pwads_count'] > 0:
            for i in range(0, self.query_dict['optional_pwads_count']):
                self.query_dict['optional_pwads'].append(self._next_string())
        # Amount of DEHACKED (*.deh) patches loaded
        self.query_dict['deh_loaded'] = self._next_bytes(1)
        # DEHACKED patch name (one string for each .deh patch)
        self.query_dict['deh_list'] = []
        if self.query_dict['deh_loaded'] > 0:
            for i in range(0, self.query_dict['deh_loaded']):
                self.query_dict['deh_list'].append(self._next_string())
        # End of raw query data.

        # TODO: SQF2 extended flags

    @property
    def version(self) -> str:
        """:class:`str`: Returns the host's version."""
        return self.query_dict['version']

    @property
    def name(self) -> str:
        """:class:`str`: Returns the host's name."""
        return self.query_dict['hostname']

    @property
    def url(self) -> str:
        """:class:`str`: Returns the host's URL website.
        Uses for downloading PWADs from self-hosted."""
        return self.query_dict['url']

    @property
    def map(self) -> str:
        """:class:`str`: Returns the host's current game map."""
        return self.query_dict['map']

    @property
    def max_clients(self) -> int:
        """:class:`int`: Returns the host's maximum clients in host."""
        return self.query_dict['maxclients']

    @property
    def max_players(self) -> int:
        """:class:`int`: Returns the host's maximum players in game."""
        return self.query_dict['maxplayers']

    @property
    def pwads_loaded(self) -> int:
        """:class:`int`: Returns the count of loaded PWADs in host."""
        return self.query_dict['pwads_loaded']

    @property
    def pwads(self) -> list:
        """:class:`list`: Returns the list of loaded PWADs in host."""
        return self.query_dict['pwads_list']

    @property
    def gamemode(self) -> enums.Gamemode:
        """:class:`Gamemode`: Returns the host's current game mode."""
        return self.query_dict['gamemode']

    @property
    def instagib(self) -> bool:
        """:class:`bool`: Returns True if Instagib modifier
        is enabled on the host."""
        return self.query_dict['instagib']

    @property
    def buckshot(self) -> bool:
        """:class:`bool`: Returns True if Buckshot modifier
        is enabled on the host."""
        return self.query_dict['buckshot']

    @property
    def gamename(self) -> str:
        """:class:`str`: Returns host's game name from IWAD."""
        return self.query_dict['gamename']

    @property
    def iwad(self) -> str:
        """:class:`str`: Returns host's current IWAD filename."""
        return self.query_dict['iwad']

    @property
    def force_password(self) -> bool:
        """:class:`bool`: Returns True if host forces password
        for connection."""
        return self.query_dict['forcepassword']

    @property
    def force_join_password(self) -> bool:
        """:class:`bool`: Returns True if host forces password
        for joining the game."""
        return self.query_dict['forcejoinpassword']

    @property
    def skill(self) -> int:
        """:class:`int`: Returns the host's game skill."""
        return self.query_dict['skill']

    @property
    def bot_skill(self) -> int:
        """:class:`int`: Returns the host's bot skill."""
        return self.query_dict['botskill']

    @property
    def frag_limit(self) -> int:
        """:class:`int`: Returns the game's frag limit."""
        return self.query_dict['fraglimit']

    @property
    def time_limit(self) -> int:
        """:class:`int`: Returns the game's time limit."""
        return self.query_dict['timelimit']

    @property
    def time_limit_left(self) -> int:
        """:class:`int`: Returns the game's time limit left in minutes."""
        return self.query_dict['timelimit_left']

    @property
    def duel_limit(self) -> int:
        """:class:`int`: Returns the game's duels limit."""
        return self.query_dict['duellimit']

    @property
    def point_limit(self) -> int:
        """:class:`int`: Returns the game's points limit in CTF."""
        return self.query_dict['pointlimit']

    @property
    def win_limit(self) -> int:
        """:class:`int`: Returns the game's win count limit."""
        return self.query_dict['winlimit']

    @property
    def number_players(self) -> int:
        """:class:`int`: Returns the host's number of players in game."""
        return self.query_dict['numplayers']

    @property
    def email(self) -> str:
        """:class:`str`: Returns the host's E-Mail address."""
        return self.query_dict['hostemail']

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
