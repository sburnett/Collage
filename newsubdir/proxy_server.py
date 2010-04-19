#!/usr/bin/env python

from donation.database import AppDatabase
import datetime
import time
from optparse import OptionParser
import threading

from collage.messagelayer import MessageLayer

from tasks import DonateTagPairFlickrTask
from providers import DonatedVectorProvider
from instruments import timestamper

import proxy_common as common

NEWS_PERIOD = datetime.timedelta(1,)
UPDATE_PERIOD = datetime.timedelta(1,)

def send_news(address, data, database, tags, send_ratio, killswitch):
    tag_pairs = [(a, b) for a in tags for b in tags if a < b]
    tasks = map(lambda pair: DonateTagPairFlickrTask(pair, database), tag_pairs)
    vector_provider = DonatedVectorProvider(database, killswitch)

    message_layer = MessageLayer(vector_provider,
                                 common.BLOCK_SIZE,
                                 common.MAX_UNIQUE_BLOCKS,
                                 tasks,
                                 common.TASKS_PER_MESSAGE,
                                 timestamper)

    message_layer.send(address, data, send_ratio=send_ratio)

def get_news(today):
    return 'Nothing interesting happened on %d-%d-%d' % (today.year, today.month, today.day)

def get_tags():
    tags_file = 'flickr_tags'
    tags = []
    for line in open(tags_file, 'r'):
        tags.append(line.strip())
    return tags

def main():
    usage = 'usage: %s [options] <db_dir>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(send_ratio=100)
    parser.add_option('-r', '--send-ratio',
                      dest='send_ratio', action='store', type='float',
                      help='Ratio between data to send and total data length')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify donation database directory')

    while True:
        today = datetime.datetime.utcnow()
        address = common.format_address(today)

        data = get_news(today)
        database = AppDatabase(args[0], 'proxy')
        tags = get_tags()

        killswitch = threading.Event()

        thread = threading.Thread(target=send_news,
                                  args=(address, data, database, tags, options.send_ratio, killswitch))

        while today.day == datetime.datetime.utcnow().day:
            time.sleep(1)

        if thread.is_alive():
            killswitch.set()
            thread.join()

if __name__ == '__main__':
    main()
