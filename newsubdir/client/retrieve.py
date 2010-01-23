#!/usr/bin/env python

import sys
import xmlrpclib
from optparse import OptionParser

def main():
    usage = 'usage: %s [options] <key>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(url='http://127.0.0.1:8000')
    parser.add_option('-u', '--url', dest='url', action='store', type='string', help='Server URL')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify key')

    proxy = xmlrpclib.ServerProxy(options.url)
    data = proxy.retrieve(args[0])
    
    if data == '':
        sys.stderr.write('No data available\n')
        sys.exit(1)

    sys.stdout.write(data.data)
    sys.exit(0)

if __name__ == '__main__':
    main()
