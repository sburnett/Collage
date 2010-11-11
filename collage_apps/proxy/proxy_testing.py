#!/usr/bin/env python
"""Demo Collage application that reads news articles published by the server.

We call this application a "proxy", because it could be used to serve any Web
content.

"""

import threading
import datetime
import sqlite3
from optparse import OptionParser
import os.path

from selenium.firefox.webdriver import WebDriver

from collage.messagelayer import MessageLayer, MessageLayerError
from collage.instrument import CollageStatus

from collage_apps.providers.local import NullVectorProvider
from collage_apps.instruments import Timestamper

import proxy_common as common

import pdb

class Snippet(object):
    def __init__(self, module, command):
        self.module = module
        self.command = command

    def get_module(self):
        return self.module

    def execute(self, driver):
        pkg = __import__('collage_apps.proxy.taskmodules', fromlist=[str(self.module)])
        mod = pkg.__getattribute__(self.module)
        return eval(self.command, mod.__dict__, {'driver': driver})

def get_snippets(task_list, options):
    if task_list == 'centralized':
        return [Snippet('flickr_user', 'WebUserFlickrTask(driver, %s)' % repr('srburnet'))]
    elif task_list == 'community':
        return [Snippet('flickr_new', 'WebTagPairFlickrTask(driver, %s)' % repr(('nature', 'vacation')))]
    elif task_list == 'local':
        return [Snippet('local', 'ReadDirectory(%s)' % repr(options.local_dir))]

def download(address, snippets):
    driver = WebDriver()

    tasks = []
    for snippet in snippets:
        tasks.append(snippet.execute(driver))

    vector_provider = NullVectorProvider()
    message_layer = MessageLayer(vector_provider,
                                 common.BLOCK_SIZE,
                                 common.MAX_UNIQUE_BLOCKS,
                                 tasks,
                                 common.TASKS_PER_MESSAGE,
                                 Timestamper(),
                                 mac=True)
    try:
        data = message_layer.receive(address)
    except MessageLayerError:
        pass

    driver.close()

    return data

def main():
    usage = 'usage: %s <task list> [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(localdir=None)
    parser.add_option('-l', '--local-dir',
                      dest='localdir',
                      action='store',
                      type='string',
                      help='Local content host directory (testing)')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Possible task lists: centralized, community or local')

    address = common.format_address(datetime.datetime.utcnow())
    snippets = get_snippets(args[0], options)

    data = download(address, snippets)
    print 'Retrieved article of length %d' % len(data)

if __name__ == '__main__':
    main()
