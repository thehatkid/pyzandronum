class QueryDenied(Exception):
    """
    Raises when server query request was denied.
    """

    def __str__(self):
        return 'Server query request was denied by server'


class QueryIgnored(QueryDenied):
    """
    Raises if your IP has made a request in the past
    sv_queryignoretime seconds.
    """

    def __str__(self):
        return 'Query denied; Your IP has made a request in the past seconds'


class QueryBanned(QueryDenied):
    """
    Raises if your IP was banned by server.
    """

    def __str__(self):
        return 'Query denied; Your IP was banned from this server.'
