#!/usr/bin/env python2
"""A command-line interface to poll for completion of vector donation.

If the indicated vector is available, it will be printed to stdout and the
script will exit with return code 0. Otherwise, nothing will be printed to
stdout and the script will exit with return code 1.

"""

import sys
from optparse import OptionParser

from rpc import retrieve

def main():
    usage = 'usage: %s [options] <key>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(url='https://127.0.0.1:8000/server.py')
    parser.add_option('-u', '--url', dest='url', action='store', type='string', help='Server URL')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify key')

    data = retrieve(options.url, args[0])

    if data == '':
        sys.stderr.write('No data available\n')
        sys.exit(1)

    sys.stdout.write(data.data)
    sys.exit(0)

if __name__ == '__main__':
    main()
