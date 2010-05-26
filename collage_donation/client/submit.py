#!/usr/bin/env python

import sys
from optparse import OptionParser

from rpc import submit

def main():
    usage = 'usage: %s [options] <application>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(url='https://127.0.0.1:8000/server.py', attributes=[], expiration=86400)
    parser.add_option('-u', '--url', dest='url', action='store', type='string', help='Server URL')
    parser.add_option('-a', '--attribute', dest='attributes', action='append', type='string', help='Vector attributes')
    parser.add_option('-l', '--lifetime', dest='expiration', action='store', type='int', help='Lifetime of request')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify application name')

    data = sys.stdin.read()
    application = args[0]
    attrs = []
    for attr in options.attributes:
        attrs.append(tuple(attr.split(':', 1)))
    key = submit(options.url, data, application, attrs, options.expiration)
    sys.stdout.write(key)

if __name__ == '__main__':
    main()
