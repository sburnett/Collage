import re
import datetime
import base64
import hashlib

BLOCK_SIZE = 8
MAX_UNIQUE_BLOCKS = 2**16
TASKS_PER_MESSAGE = 1
UPDATE_ADDRESS = 'proxy://update'

def format_address(today):
    return 'proxy://news/%.4d/%.2d/%.2d' % (today.year, today.month, today.day)

def parse_address(address):
    match = re.match(r'proxy://news/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)', address)
    return datetime.date(int(match.group('year')),
                         int(match.group('month')),
                         int(match.group('day')))

def main():
    print format_address(datetime.datetime.utcnow())

if __name__ == '__main__':
    main()
