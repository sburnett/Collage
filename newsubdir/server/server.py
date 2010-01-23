#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer
import xmlrpclib
from optparse import OptionParser
import datetime

import database

def main():
    usage = 'usage: %s [options] <database> <vectors_dir> <application_name>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(host='127.0.0.1', port='8000')
    parser.add_option('-H', '--host', dest='host', action='store', type='string', help='Server hostname')
    parser.add_option('-p', '--port', dest='port', action='store', type='int', help='Server port')
    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error('Need to specify database, vectors directory and application name')

    db = database.DonationDatabase(args[0], args[2], args[1])

    def donate(data, application, attributes, expiration=86400):
        tdexpiration = datetime.timedelta(0, expiration)
        return db.donate(data.data, application, attributes, tdexpiration)

    def retrieve(key):
        data = db.collect(key)
        if data is None:
            return ''
        else:
            return xmlrpclib.Binary(data)

    server = SimpleXMLRPCServer((options.host, options.port))
    server.register_function(donate, 'donate')
    server.register_function(retrieve, 'retrieve')
    server.serve_forever()

if __name__ == '__main__':
    main()
