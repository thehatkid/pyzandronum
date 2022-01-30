"""
Asynchronous UDP module for pyzandronum.
"""

import asyncio


class ClosedError(Exception):
    pass


class SocketProtocol:
    def __init__(self):
        self._packets = asyncio.Queue()

    def connection_made(self, transport):
        pass

    def connection_lost(self, transport):
        self._packets.put_nowait(None)

    def datagram_received(self, data, addr):
        self._packets.put_nowait((data, addr))

    async def recvfrom(self):
        return await self._packets.get()


class Socket:
    """A UDP socket.
    Use :func:`~pyzandronum.asyncudp.create_socket()` to create an instance of
    this class."""

    def __init__(self, transport, protocol):
        self._transport = transport
        self._protocol = protocol

    def close(self):
        """Close the socket."""
        self._transport.close()

    def sendto(self, data, addr=None):
        """Send given packet to given address ``addr``. Sends to
        ``remote_addr`` given to the constructor if ``addr`` is ``None``."""
        self._transport.sendto(data, addr)

    async def recvfrom(self):
        """Receive a UDP packet.
        Raises ClosedError on connection error, often by calling the close()
        method from another task."""
        packet = await self._protocol.recvfrom()

        if packet is None:
            raise ClosedError()

        return packet

    def getsockname(self):
        """Get bound infomation."""
        return self._transport.get_extra_info('sockname')

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        self.close()


async def create_socket(local_addr=None, remote_addr=None):
    """Create a UDP socket with given local and remote addresses."""
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        SocketProtocol,
        local_addr=local_addr,
        remote_addr=remote_addr
    )
    return Socket(transport, protocol)