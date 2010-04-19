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

import flickrapi

from collage.messagelayer import MessageLayer

from tasks import TagPairFlickrTask
from vectors import OutguessVector
from providers import NullVectorProvider, DirectoryVectorProvider
from instruments import timestamper

def auth_flickr():
    """Authenticate with Flickr using our api key and secret.

    The user will be prompted to authenticate using his
    account if needed."""

    api_key = 'ebc4519ce69a3485469c4509e8038f9f'
    api_secret = '083b2c8757e2971f'

    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='delete')
    if not token:
        raw_input('Press ENTER after you have authorized this program')
    flickr.get_token_part_two((token, frob))
    return flickr

def main():
    usage = 'usage: %s [options] <send|receive|delete> <id>'
    parser = OptionParser(usage=usage)
    parser.set_defaults()
    parser.add_option('-f', '--file',
                      dest='filename', action='store',
                      type='string', help='File to send')
    parser.add_option('-n', '--num-photos',
                      dest='num_vectors', action='store',
                      type='int', help='Number of photos to send')
    parser.add_option('-r', '--send-ratio',
                      dest='send_ratio', action='store', type='float',
                      help='Ratio between data to send and total data length')
    parser.add_option('-d', '--directory',
                      dest='directory', action='store', type='string',
                      help='Directory to read photos from')
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

    flickr = auth_flickr()

    tags = []
    for line in open(options.tagsfile, 'r'):
        tags.append(line.strip())
    tag_pairs = [(a, b) for a in tags for b in tags if a < b]
    tasks = map(lambda pair: TagPairFlickrTask(flickr, pair), tag_pairs)

    if args[0] == 'send':
        if options.directory is None:
            parser.error('Must specify a directory with JPEGs in it, to embed and upload.')

        vector_provider = DirectoryVectorProvider(OutguessVector,
                                                  options.directory,
                                                  ['.jpeg', '.jpg'])

        if options.filename is None:
            print 'Enter message and press <Ctrl-D>'
            data = sys.stdin.read()
        else:
            data = open(options.filename, 'r').read()

        message_layer = MessageLayer(vector_provider,
                                     block_size,
                                     max_unique_blocks,
                                     tasks,
                                     tasks_per_message,
                                     timestamper)
        if options.num_vectors is not None:
            message_layer.send(args[1], data, num_vectors=options.num_vectors)
        elif options.send_ratio is not None:
            message_layer.send(args[1], data, send_ratio=options.send_ratio)
        else:
            message_layer.send(args[1], data)
    elif args[0] == 'receive':
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
        results = flickr.photos_search(user_id='me')
        for photo in results[0]:
            #if photo.attrib['title'] == base64.b64encode(args[1]):
                flickr.photos_delete(photo_id=photo.attrib['id'])
    else:
        parser.error('Invalid action')

if __name__ == '__main__':
    main()
