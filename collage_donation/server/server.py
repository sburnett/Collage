#!/usr/bin/env python

from SimpleXMLRPCServer import SimpleXMLRPCServer, CGIXMLRPCRequestHandler
import xmlrpclib
from optparse import OptionParser
import datetime
import os
import os.path
import sys

import thfcgi

from database import DonaterDatabase

def prep_funcs(db_dir):
    def donate(data, application, attributes, expiration=86400):
        db = DonaterDatabase(db_dir)
        tdexpiration = datetime.timedelta(0, expiration)
        return db.donate(data.data, application, attributes, tdexpiration)

    def retrieve(key):
        db = DonaterDatabase(db_dir)
        data = db.collect(key)
        if data is None:
            return ''
        else:
            return xmlrpclib.Binary(data)

    def update_attributes(*args):
        db = DonaterDatabase(db_dir)
        db.update_attributes(*args)
        return ''

    return (donate, retrieve, update_attributes)

class CGIHandler:
    def __init__(self, handler):
        self.handler = handler

    def handle_request(self, req, env, form):
        try:
            response = self.handler._marshaled_dispatch(form.file.read())
            http_headers = [ "Content-Type: text/xml"
                           , "Content-Length: %d" % len(response)
                           , "Cache-Control: no-cache"
                           , "Pragma: no-cache"
                           , "Expires: 0"
                           , "\r\n"
                           ]

            req.out.write('\r\n'.join(http_headers))
            req.out.write(response)
            req.finish()
        except SystemExit:
            pass
        except Exception, e:
            import traceback
            f = open("fastcgi_errors.log", "a")
            traceback.print_exc(file=f)
            f.close()

def main():
    db_dir = sys.argv[1]
    (donate, retrieve, update_attributes) = prep_funcs(db_dir)

    handler = CGIXMLRPCRequestHandler()
    handler.register_function(donate)
    handler.register_function(retrieve)
    handler.register_function(update_attributes)
    thfcgi.THFCGI(CGIHandler(handler).handle_request).run()

#def main():
#    usage = 'usage: %s [options] <database_dir>'
#    parser = OptionParser(usage=usage)
#    parser.set_defaults(host='127.0.0.1', port='8000')
#    parser.add_option('-H', '--host', dest='host', action='store', type='string', help='Server hostname')
#    parser.add_option('-p', '--port', dest='port', action='store', type='int', help='Server port')
#    (options, args) = parser.parse_args()
#
#    if len(args) != 1:
#        parser.error('Need to specify database directory')
#
#    (donate, retrieve, update_attributes) = prep_funcs(args[0])
#
#    server = SimpleXMLRPCServer((options.host, options.port))
#    server.register_function(donate, 'donate')
#    server.register_function(retrieve, 'retrieve')
#    server.register_function(update_attributes, 'update_attributes')
#    server.serve_forever()

if __name__ == '__main__':
    if 'SERVER_NAME' in os.environ:
        handle_cgi()
    else:
        main()
