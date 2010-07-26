#!/usr/bin/env python

from collage_donation.server.database import AppDatabase
import datetime
import time
from optparse import OptionParser
import threading
import urllib
import re
import base64
import shelve

from collage.messagelayer import MessageLayer

from collage_apps.tasks.flickr import DonateTagPairFlickrTask
from collage_apps.tasks.local import DonateDirectoryTask
from collage_apps.providers.flickr import DonatedVectorProvider
from collage_apps.instruments import timestamper

import proxy_common as common

def send_news(address, data, db_dir, tags, send_ratio, killswitch, local_dir, estimate_db):
    database = AppDatabase(db_dir, 'proxy')

    tasks = []
    #tag_pairs = [(a, b) for a in tags for b in tags if a < b]
    #tasks.extend(map(lambda pair: DonateTagPairFlickrTask(pair, database), tag_pairs))
    if local_dir is not None:
        tasks.append(DonateDirectoryTask(local_dir, address, database))

    vector_provider = DonatedVectorProvider(database, killswitch, estimate_db)

    message_layer = MessageLayer(vector_provider,
                                 common.BLOCK_SIZE,
                                 common.MAX_UNIQUE_BLOCKS,
                                 tasks,
                                 common.TASKS_PER_MESSAGE,
                                 timestamper,
                                 mac=True)

    #print 'Sending message: %s' % data

    message_layer.send(address, data, send_ratio=send_ratio)

def get_news(today):
    urls = []

    pagedata = urllib.urlopen('http://www.bbc.co.uk/news/mobile').read()
    matches = re.finditer(r'<a class="promoLink" href="(?P<link>.*?)">', pagedata)
    for match in matches:
        urls.append(match.group('link'))
    matches = re.finditer(r'<li class="listTxt">\s*<a href="(?P<link>.*?)">', pagedata)
    for match in matches:
        urls.append(match.group('link'))

    stories = []
    for url in urls:
        if url.startswith('http://'):
            continue

        pagedata = urllib.urlopen('http://www.bbc.co.uk%s' % url).read()
        pagedata = re.sub(r'<!--.*?-->', '', pagedata)
        pagedata = re.sub(r'(?ims)<form(>|\s).*?</form>', '', pagedata)
        pagedata = re.sub(r'\s+', ' ', pagedata)

        match = re.search(r'(?P<title><h1>.*?</h1>).*?<div class="storybody">(?P<story>.*?)</div>\s*<div', pagedata, re.I|re.S)
        if match is None:
            print "Couldn't parse %s" % url
        else:
            stories.append('<div>' + match.group('title') + match.group('story') + '</div>')

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
    parser.set_defaults(send_ratio=100, local_dir=None, estimate_db='estimate_db')
    parser.add_option('-r', '--send-ratio', dest='send_ratio',
                      action='store', type='float',
                      help='Ratio between data to send and total data length')
    parser.add_option('-d', '--local-dir', dest='local_dir',
                      action='store', type='string',
                      help='Local content host directory (for testing)')
    parser.add_option('-e', '--estimate-db', dest='estimate_db',
                      action='store', type='string',
                      help='Location of capacity estimation database')
    (options, args) = parser.parse_args()

    estimate_db = shelve.open(options.estimate_db, writeback=True)

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
                                  args=(address, data, db_dir, tags, options.send_ratio, killswitch, options.local_dir, estimate_db))
        thread.daemon = True
        thread.start()

        while today.day == datetime.datetime.utcnow().day:
            time.sleep(1)

        if thread.is_alive():
            killswitch.set()
            thread.join()

if __name__ == '__main__':
    main()
