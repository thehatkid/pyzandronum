import pyzandronum

# You can put your IP address and port to query.
server = pyzandronum.Server('195.2.236.130', 6665)

# Get server info by querying
server.query()

# Output server info
print('Host Name:', server.name)
print('Current Game Map:', server.map)
print('Online Players: {0}/{1} (max clients: {2})'.format(
    server.number_players,
    server.max_players,
    server.max_clients
))
print('PWADs: {0} (total loaded: {1})'.format(
    server.pwads,
    server.pwads_loaded
))
print('IWAD filename:', server.iwad, '| IWAD name:', server.gamename)
print('Game mode:', server.gamemode)
