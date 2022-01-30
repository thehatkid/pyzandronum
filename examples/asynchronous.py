import asyncio
from pyzandronum import AsyncServer

loop = asyncio.get_event_loop()


async def counter():
    for i in range(1, 6):
        await asyncio.sleep(1.0)
        print('[Counter]', i)
    loop.stop()


async def main():
    await asyncio.sleep(3.0)
    print('[Query] Querying host...')
    async with AsyncServer('195.2.236.130', 6665) as server:
        print('[Query] Server Name:', server.name)
        print('[Query] Online: {0}/{1} (max clients: {2})'.format(
            server.number_players,
            server.max_players,
            server.max_clients
        ))
        print('[Query] Map: {0} | Gamemode: {1}'.format(
            server.map,
            server.gamemode
        ))


loop.create_task(counter())
loop.create_task(main())

loop.run_forever()
