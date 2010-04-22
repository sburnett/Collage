#!/usr/bin/env python

from optparse import OptionParser
import time

from database import CleanupDatabase

PAUSE_TIME = 60

def main():
    usage = 'usage: %s [options] <database_dir>'
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify database directory')

    db = CleanupDatabase(args[0])

    while True:
        db.cleanup()
        time.sleep(PAUSE_TIME)

if __name__ == '__main__':
    main()
