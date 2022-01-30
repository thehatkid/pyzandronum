import pyzandronum

# You can put your IP address and port to query.
server = pyzandronum.Server('195.2.236.130', 6665)

# Get server info by querying
server.query()

# Output players info
if len(server.players) > 0:
    for player in server.players:
        print(f'[ {player.name} ]')
        print(f'  |--> Ping: {player.ping}ms, Score: {player.score}, Time: {player.time} minutes')
        print(f'  |--> Spectating? {player.spectator}, Bot? {player.bot}')
        print('')
else:
    print('No players online to show.')
