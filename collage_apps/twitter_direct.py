#!/usr/bin/env python

import sys
import os.path
import base64
from optparse import OptionParser
import math
import time

import twitter

from collage.messagelayer import MessageLayer

from collage_apps.tasks.twitter import DirectTwitterTask
from collage_apps.vectors.tweet import BlatantVector, AllCapsVector
from collage_apps.providers.local import NullVectorProvider, DirectoryVectorProvider
from collage_apps.instruments import timestamper

def usage():
    print '%s send <id> <message_file> <num_vectors>' % sys.argv[0]
    print '%s receive <id>' % sys.argv[0]
    sys.exit(1)

def main():
    usage = 'usage: %s [options] <send|recieve> <id>'
    parser = OptionParser(usage=usage)
    parser.add_option('-u', '--username', dest='username', action='store', type='string', help='Twitter username')
    parser.add_option('-p', '--password', dest='password', action='store', type='string', help='Twitter password')
    parser.add_option('-f', '--file', dest='filename', action='store', type='string', help='File to send')
    parser.add_option('-n', '--num-tweets', dest='num_vectors', action='store', type='int', help='Number of tweets to send')
    parser.add_option('-r', '--send-ratio', dest='send_ratio', action='store', type='float', help='Ratio between data to send and total data length')
    parser.add_option('-d', '--directory', dest='directory', action='store', type='string', help='Directory to read tweets from')
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error('Need to specify action and message id')

    block_size = 8
    max_unique_blocks = 2**8
    tasks_per_message = 3

    snippets_path = os.path.abspath('snippets')

    if args[0] == 'send':
        if options.username is None or options.password is None:
            parser.error('Must specify Twitter username and password to send messages.')
        if options.directory is None:
            parser.error('Must specify a directory with tweets (*.tweet) in it, to embed and upload.')

        vector_provider = DirectoryVectorProvider(AllCapsVector,
                                                  options.directory,
                                                  '.tweet')

        if options.filename is None:
            print 'Enter message and press <Ctrl-D>'
            data = sys.stdin.read()
        else:
            data = open(options.filename, 'r').read()

        api = twitter.Api(username=options.username, password=options.password)
        tasks = [DirectTwitterTask(api, options.username, AllCapsVector)]
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
        if options.username is None:
            parser.error('Must specify username to search')

        vector_provider = NullVectorProvider()

        api = twitter.Api()
        tasks = [DirectTwitterTask(api, options.username, AllCapsVector)]
        message_layer = MessageLayer(vector_provider,
                                     block_size,
                                     max_unique_blocks,
                                     tasks, 
                                     tasks_per_message,
                                     timestamper)
        data = message_layer.receive(args[1])
        sys.stdout.write(data)
    elif args[0] == 'delete':
        if options.username is None or options.password is None:
            parser.error('Must specify Twitter username and password to delete messages.')

        api = twitter.Api(username=options.username, password=options.password)
        results = api.GetUserTimeline(options.username)
        for status in results:
            api.DestroyStatus(status.GetId())
            time.sleep(1)
    else:
        parser.error('Invalid action')

if __name__ == '__main__':
    main()
