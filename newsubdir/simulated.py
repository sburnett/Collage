#!/usr/bin/env python
'''
This application simulates a variety of other Collage applications, for
performance evaluation.
'''

import sys
import os
import os.path
from optparse import OptionParser
import base64
import time
import random

import flickrapi

from collage.messagelayer import MessageLayer

from tasks import SimulatedTask
from vectors import SimulatedVector
from providers import NullVectorProvider, SimulatedVectorProvider
from instruments import timestamper

def main():
    usage = 'usage: %s [options] <send|receive|delete> <id>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(mapping_size=1, encoding_rate=0.1, encoding_deviation=0.0,
                        task_overhead=0.0, task_deviation=0.0, database_size=1,
                        time_overhead=0, time_deviation=0, upload=128, download=768,
                        vectors_per_task=1,
                        vector_length=200000, vector_deviation=10000)
    parser.add_option('-f', '--file',
                      dest='filename', action='store',
                      type='string', help='File to send')
    parser.add_option('-n', '--num-vectors',
                      dest='num_vectors', action='store',
                      type='int', help='Number of vectors to send')
    parser.add_option('-s', '--database-size',
                      dest='database_size', action='store',
                      type='int', help='Size of task database')
    parser.add_option('-m', '--mapping-size',
                      dest='mapping_size', action='store',
                      type='int', help='Size of task mapping')
    parser.add_option('-r', '--send-ratio',
                      dest='send_ratio', action='store', type='float',
                      help='Ratio between data to send and total data length')
    parser.add_option('-e', '--encoding-rate',
                      dest='encoding_rate', action='store', type='float',
                      help='Vector encoding rate')
    parser.add_option('-E', '--encoding-deviation',
                      dest='encoding_deviation', action='store', type='float',
                      help='Vector encoding deviation')
    parser.add_option('-l', '--vector-length',
                      dest='vector_length', action='store', type='int',
                      help='Average vector length in bytes')
    parser.add_option('-L', '--vector-deviation',
                      dest='vector_deviation', action='store', type='int',
                      help='Vector length deviation')
    parser.add_option('-t', '--task-overhead',
                      dest='task_overhead', action='store', type='int',
                      help='Task overhead in bytes')
    parser.add_option('-T', '--task-deviation',
                      dest='task_deviation', action='store', type='int',
                      help='Task overhead deviation, in bytes')
    parser.add_option('-v', '--vectors-per-task',
                      dest='vectors_per_task', action='store', type='int',
                      help='Number of vectors for each task')
    parser.add_option('-p', '--time-overhead',
                      dest='time_overhead', action='store', type='float',
                      help='Time overhead in seconds')
    parser.add_option('-P', '--time-deviation',
                      dest='time_deviation', action='store', type='float',
                      help='Time overhead deviation')
    parser.add_option('-u', '--upload-rate',
                      dest='upload', action='store', type='int',
                      help='Upload rate, in Kbps')
    parser.add_option('-d', '--download-rate',
                      dest='download', action='store', type='int',
                      help='Download rate, in Kbps')
    parser.add_option('-D', '--storage-directory',
                      dest='storage_dir', action='store', type='string',
                      help='Storage directory for published vectors')
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.error('Need to specify action and message id')

    if options.storage_dir is None:
        parser.error('Must specify vector storage directory')

    block_size = 32
    max_unique_blocks = 2**16

    tasks = []
    for i in range(options.database_size):
        overhead = random.gauss(options.task_overhead, options.task_deviation)
        task = SimulatedTask(overhead,
                             options.time_overhead, options.time_deviation,
                             options.download, options.upload,
                             options.vectors_per_task,
                             options.storage_dir)
        tasks.append(task)

    if args[0] == 'send':
        vector_provider = SimulatedVectorProvider(SimulatedVector,
                                                  options.encoding_rate,
                                                  options.encoding_deviation,
                                                  options.vector_length,
                                                  options.vector_deviation)

        if options.filename is None:
            print 'Enter message and press <Ctrl-D>'
            data = sys.stdin.read()
        else:
            data = open(options.filename, 'r').read()

        message_layer = MessageLayer(vector_provider,
                                     block_size,
                                     max_unique_blocks,
                                     tasks,
                                     options.mapping_size,
                                     timestamper,
                                     256)
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
                                     options.mapping_size,
                                     timestamper)
        data = message_layer.receive(args[1])
        sys.stdout.write(data)
    elif args[0] == 'delete':
        for filename in os.listdir(options.storage_dir):
            if os.path.splitext(filename)[1] == '.vector':
                os.unlink(os.path.join(options.storage_dir, filename))
    else:
        parser.error('Invalid action')

if __name__ == '__main__':
    main()
