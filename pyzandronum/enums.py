import enum


class RequestFlags(enum.Flag):
    """
    Zandronum request flags for querying.
    """

    NONE = 0x0

    SQF_NAME = 0x00000001
    SQF_URL = 0x00000002
    SQF_EMAIL = 0x00000004
    SQF_MAPNAME = 0x00000008
    SQF_MAXCLIENTS = 0x00000010
    SQF_MAXPLAYERS = 0x00000020
    SQF_PWADS = 0x00000040
    SQF_GAMETYPE = 0x00000080
    SQF_GAMENAME = 0x00000100
    SQF_IWAD = 0x00000200
    SQF_FORCEPASSWORD = 0x00000400
    SQF_FORCEJOINPASSWORD = 0x00000800
    SQF_GAMESKILL = 0x00001000
    SQF_BOTSKILL = 0x00002000
    SQF_DMFLAGS = 0x00004000 # deprecated
    SQF_LIMITS = 0x00010000
    SQF_TEAMDAMAGE = 0x00020000
    SQF_TEAMSCORES = 0x00040000 # deprecated
    SQF_NUMPLAYERS = 0x00080000
    SQF_PLAYERDATA = 0x00100000
    SQF_TEAMINFO_NUMBER = 0x00200000
    SQF_TEAMINFO_NAME = 0x00400000
    SQF_TEAMINFO_COLOR = 0x00800000
    SQF_TEAMINFO_SCORE = 0x01000000
    SQF_TESTING_SERVER = 0x02000000
    SQF_DATA_MD5SUM = 0x04000000 # deprecated
    SQF_ALL_DMFLAGS = 0x08000000
    SQF_SECURITY_SETTINGS = 0x10000000
    SQF_OPTIONAL_WADS = 0x20000000
    SQF_DEH = 0x40000000
    SQF_EXTENDED_INFO = 0x80000000

    @classmethod
    def all(self):
        retval = self.NONE
        for member in self.__members__.values():
            retval |= member
        return retval

    @classmethod
    def default(self):
        return (
            self.SQF_NAME |
            self.SQF_URL |
            self.SQF_EMAIL |
            self.SQF_MAPNAME |
            self.SQF_MAXCLIENTS |
            self.SQF_MAXPLAYERS |
            self.SQF_PWADS |
            self.SQF_GAMETYPE |
            self.SQF_GAMENAME |
            self.SQF_IWAD |
            self.SQF_FORCEPASSWORD |
            self.SQF_FORCEJOINPASSWORD |
            self.SQF_GAMESKILL |
            self.SQF_BOTSKILL |
            self.SQF_LIMITS |
            self.SQF_NUMPLAYERS |
            self.SQF_PLAYERDATA |
            self.SQF_TESTING_SERVER |
            self.SQF_ALL_DMFLAGS |
            self.SQF_SECURITY_SETTINGS |
            self.SQF_OPTIONAL_WADS |
            self.SQF_DEH
        )


class Response(enum.Enum):
    """
    Zandronum magic accepted number responses.
    """

    ACCEPTED = 5660023
    DENIED_QUERY = 5660024
    DENIED_BANNED = 5660025
