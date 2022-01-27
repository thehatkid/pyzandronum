import pyzandronum

# You can put your IP address and port to query.
server = pyzandronum.Server('195.2.236.130', 6665)

# Get server info by querying
server.query()

# Output server info
print('Server Name:', server._query_dict['hostname'])
print('Current Map:', server._query_dict['map'])
print('Online Players: {0}/{1} (max clients: {2})'.format(
    server._query_dict['numplayers'],
    server._query_dict['maxplayers'],
    server._query_dict['maxclients']
))
print('PWADs: {0} (total loaded: {1})'.format(
    server._query_dict['pwads_list'],
    server._query_dict['pwads_loaded']
))
print('IWAD:', server._query_dict['iwad'])
