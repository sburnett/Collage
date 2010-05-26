#!/usr/bin/env python
'''
This Collage application implements a simple proxy server based on Flickr.

The task scheme used for this proxy is "direct", since files are uploaded and
downloaded without regard to deniability.
'''

import sys
from optparse import OptionParser
import base64
import time

from selenium.firefox.webdriver import WebDriver

from collage.messagelayer import MessageLayer

from collage_apps.tasks.flickr import WebTagPairFlickrTask
from collage_apps.vectors.jpeg import OutguessVector
from collage_apps.providers.local import NullVectorProvider, DirectoryVectorProvider
from collage_apps.instruments import timestamper

def main():
    usage = 'usage: %s [options] <send|receive|delete> <id>'
    parser = OptionParser(usage=usage)
    parser.set_defaults()
    parser.add_option('-t', '--tags-file',
                      dest='tagsfile', action='store', type='string',
                      help='File to read tags from')
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error('Need to specify action and message id')

    if options.tagsfile is None:
        parser.error('Need to specify tags file')

    block_size = 8
    max_unique_blocks = 2**16
    tasks_per_message = 3

    if args[0] == 'send':
        parser.error('Send action not implemented. Use photo donation tool.')
    elif args[0] == 'receive':
        driver = WebDriver()

        tags = []
        for line in open(options.tagsfile, 'r'):
            tags.append(line.strip())
        tag_pairs = [(a, b) for a in tags for b in tags if a < b]
        tasks = map(lambda pair: WebTagPairFlickrTask(driver, pair), tag_pairs)

        vector_provider = NullVectorProvider()
        message_layer = MessageLayer(vector_provider,
                                     block_size,
                                     max_unique_blocks,
                                     tasks,
                                     tasks_per_message,
                                     timestamper)
        data = message_layer.receive(args[1])
        sys.stdout.write(data)
    elif args[0] == 'delete':
        parser.error("Delete action not implemented. You probably don't own the photos anyway.")
    else:
        parser.error('Invalid action')

if __name__ == '__main__':
    main()
