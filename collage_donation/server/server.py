#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer, CGIXMLRPCRequestHandler
import xmlrpclib
from optparse import OptionParser
import datetime
import os
import os.path

from database import DonaterDatabase

def prep_funcs(db_dir):
    db = DonaterDatabase(db_dir)

    def donate(data, application, attributes, expiration=86400):
        tdexpiration = datetime.timedelta(0, expiration)
        return db.donate(data.data, application, attributes, tdexpiration)

    def retrieve(key):
        data = db.collect(key)
        if data is None:
            return ''
        else:
            return xmlrpclib.Binary(data)

    def update_attributes(*args):
        db.update_attributes(*args)
        return ''

    return (donate, retrieve, update_attributes)

def handle_cgi():
    db_dir = '/home/collage/vectors'

    (donate, retrieve, update_attributes) = prep_funcs(db_dir)

    handler = CGIXMLRPCRequestHandler()
    handler.register_function(donate)
    handler.register_function(retrieve)
    handler.register_function(update_attributes)
    handler.handle_request()

def main():
    usage = 'usage: %s [options] <database_dir>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(host='127.0.0.1', port='8000')
    parser.add_option('-H', '--host', dest='host', action='store', type='string', help='Server hostname')
    parser.add_option('-p', '--port', dest='port', action='store', type='int', help='Server port')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify database directory')

    (donate, retrieve, update_attributes) = prep_funcs(args[0])

    server = SimpleXMLRPCServer((options.host, options.port))
    server.register_function(donate, 'donate')
    server.register_function(retrieve, 'retrieve')
    server.register_function(update_attributes, 'update_attributes')
    server.serve_forever()

if __name__ == '__main__':
    if 'SERVER_NAME' in os.environ:
        handle_cgi()
    else:
        main()
