#!/usr/bin/env python

from collage_donation.server.database import AppDatabase
import datetime
import time
from optparse import OptionParser
import threading
import urllib
import re

from collage.messagelayer import MessageLayer

from tasks import DonateTagPairFlickrTask
from providers import DonatedVectorProvider
from instruments import timestamper

import proxy_common as common

def send_news(address, data, db_dir, tags, send_ratio, killswitch):
    database = AppDatabase(db_dir, 'proxy')

    tag_pairs = [(a, b) for a in tags for b in tags if a < b]
    tasks = map(lambda pair: DonateTagPairFlickrTask(pair, database), tag_pairs)
    vector_provider = DonatedVectorProvider(database, killswitch)

    message_layer = MessageLayer(vector_provider,
                                 common.BLOCK_SIZE,
                                 common.MAX_UNIQUE_BLOCKS,
                                 tasks,
                                 common.TASKS_PER_MESSAGE,
                                 timestamper,
                                 mac=True)

    print 'Sending message: %s' % data

    message_layer.send(address, data, send_ratio=send_ratio)

def get_news(today):
    pagedata = urllib.urlopen('http://feeds.reuters.com/reuters/topNews?format=xml').read()
    matches = re.finditer('<link>(?P<link>.*?)</link>', pagedata)
    urls = []
    for match in matches:
        urls.append(match.group('link'))

    stories = []
    for url in urls[2:]:
        pagedata = urllib.urlopen(url).read()

        match = re.search('(?P<title><h1>.*?</h1>).*<span class="focusParagraph">(?P<story>.*?)<div class="relatedTopicButtons">', pagedata, re.I|re.S)
        if match is None:
            print "Couldn't parse %s" % url
        else:
            stories.append(match.group('title') + match.group('story'))

    payload = ''.join(stories)
    return payload

def get_tags():
    pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
    match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
    block = match.group(1)

    tags = []
    for m in re.finditer('<a.*?>(.*?)</a>', block, re.S|re.I):
        tags.append(m.group(1).strip().lower())
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

        print 'Publishing document %s' % address

        data = get_news(today)
        db_dir = args[0]
        tags = get_tags()
        
        killswitch = threading.Event()

        thread = threading.Thread(target=send_news,
                                  args=(address, data, db_dir, tags, options.send_ratio, killswitch))
        thread.daemon = True
        thread.start()

        while today.day == datetime.datetime.utcnow().day:
            time.sleep(1)

        if thread.is_alive():
            killswitch.set()
            thread.join()

if __name__ == '__main__':
    main()
