class Player:
    """
    Represents a Zandronum player object.
    """

    def __init__(
        self,
        byte_stream: bytes,
        byte_pos: int,
        teamgame: bool
    ) -> None:
        self._bytestartpos = byte_pos
        self._byteendpos = 0
        self._bytepos = byte_pos
        self._raw_data = byte_stream
        self._teamgame = teamgame

        self._player_dict = {
            'name': None,
            'score': None,
            'ping': None,
            'spectator': None,
            'bot': None,
            'team': None,
            'time': None
        }

        self.parse()

    def parse(self) -> None:
        """
        Parses raw binary data from player data.
        """
        if self._byteendpos >= self._bytepos:
            return
        # Player's name
        self._player_dict['name'] = self._next_string()
        # Player's score
        self._player_dict['score'] = self._next_bytes(2)
        # Player's ping
        self._player_dict['ping'] = self._next_bytes(2)
        # Player is spectating or not
        if self._next_bytes(1):
            self._player_dict['spectator'] = True
        else:
            self._player_dict['spectator'] = False
        # Player is bot or not
        if self._next_bytes(1):
            self._player_dict['bot'] = True
        else:
            self._player_dict['bot'] = False
        # Player's Team
        if self._teamgame:
            self._player_dict['team'] = self._next_bytes(1)
        # Player's playtime in minutes
        self._player_dict['time'] = self._next_bytes(1)
        # Set our "end byte position" marker
        self._byteendpos = self._bytepos

    def __repr__(self) -> str:
        return f'<Player {self.name!r}>'

    @property
    def name(self) -> str:
        """:class:`str`: Returns the player's name (without color markers)"""
        return self._player_dict['name']

    @property
    def score(self) -> int:
        """:class:`int`: Returns the player's point/frag/kill score."""
        return self._player_dict['score']

    @property
    def ping(self) -> int:
        """:class:`int`: Returns the player's ping."""
        return self._player_dict['ping']

    @property
    def spectator(self) -> bool:
        """:class:`bool`: Returns True if player is spectating."""
        return self._player_dict['spectator']

    @property
    def bot(self) -> bool:
        """:class:`bool`: Returns True if player is bot."""
        return self._player_dict['bot']

    @property
    def team(self) -> int:
        """:class:`int`: Returns the player's team. (`None` if no team)"""
        return self._player_dict['team']

    @property
    def time(self) -> int:
        """:class:`int`: Returns the player's time in minutes."""
        return self._player_dict['time']

    def _next_string(self) -> str:
        ret_str = ''

        # Read characters until we hit a null, and add them to our string
        while int(self._raw_data[self._bytepos]) != 0:
            tmp_char = ''

            # Option 1: a normal letter (ASCII between 32-254)
            # This is easy, we just assign tmp_char and proceed
            if int(self._raw_data[self._bytepos]) > 31 and int(self._raw_data[self._bytepos]) < 255 and int(self._raw_data[self._bytepos]) != 28:
                tmp_char = chr(int(self._raw_data[self._bytepos]))

            # Option 2: color code in brackets
            # This consists of a color character (ASCII 28, hex 1c) followed
            # by a color code in brackets "[]" (ASCII 91 / 93) (ex: \x1c[b1])
            # We have another loop that reads until the endof the last
            # bracket "]". We don't process colors yet, so just skip them.
            if int(self._raw_data[self._bytepos]) == 28 and int(self._raw_data[self._bytepos + 1]) == 91:
                parse_abort = False

                while int(self._raw_data[self._bytepos]) != 93:
                    # Check to see if the string ends inside the color value.
                    if int(self._raw_data[self._bytepos]) == 0:
                        parse_abort = True
                        break
                    self._bytepos += 1

                if parse_abort == True:
                    break

            # Option 3: color code followed by single byte
            # This is the color character (ASCII 28, hex 1c), followed by
            # a single color code byte instead of brackets (ex: \x1cA)
            # This is simple, we just skip the color coder and the byte,
            # and move on with the string.
            if int(self._raw_data[self._bytepos]) == 28 and int(self._raw_data[self._bytepos + 1]) != 91:
                self._bytepos += 2
                continue

            ret_str = ret_str + tmp_char
            self._bytepos += 1

        # Advance our byte counter 1 more, to get past our null byte:
        self._bytepos += 1

        return ret_str

    def _next_bytes(self, bytes_length: int):
        ret_int = int.from_bytes(
            self._raw_data[self._bytepos:self._bytepos + bytes_length],
            byteorder='little', signed=False
        )
        self._bytepos += bytes_length
        return ret_int
