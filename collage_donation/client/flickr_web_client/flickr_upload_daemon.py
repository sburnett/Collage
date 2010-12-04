#!/usr/bin/env python

"""A daemon for uploading Flickr photos donated via the Web interface.

This is needed so that the Web application doesn't need to call back
to the donation server.

Suggested usage:

flickr_upload_daemon.py -a client:web vectors

(Ensure that directory vectors exists.) This will upload all
photos that we donated by the Web donation client.

"""

from optparse import OptionParser
import time
import os
import sqlite3
import tempfile

import flickrapi

from collage_donation.client.rpc import retrieve
from collage_apps.proxy.logger import get_logger

import pdb

logger = get_logger(__name__, 'flickr_upload')

DONATION_SERVER = 'https://127.0.0.1:8000/server.py'
PAUSE_TIME = 3

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='waiting_keys.sqlite', api_key=os.environ['FLICKR_API_KEY'], api_secret=os.environ['FLICKR_SECRET'])
    parser.add_option('-d', '--database', dest='database', action='store', type='string', help='Waiting keys database')
    parser.add_option('-k', '--flickr-api-key', dest='api_key', action='store', type='string', help='Flickr API key')
    parser.add_option('-s', '--flickr-secret', dest='api_secret', action='store', type='string', help='Flickr API secret')
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error('Invalid argument')

    conn = sqlite3.connect(options.database)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS waiting
                    (key TEXT, title TEXT, token TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tags
                    (tag TEXT, waiting_id INTEGER)''')

    logger.info('Flickr upload daemon starting')

    while True:
        keys = []
        cur = conn.execute('SELECT key FROM waiting')
        for row in cur:
            keys.append(row['key'])

        for key in keys:
            data = retrieve(DONATION_SERVER, key)
            if data != '':
                datafile = tempfile.NamedTemporaryFile(delete=False)
                datafile.write(data.data)
                datafile.close()

                cur = conn.execute('''SELECT rowid,* FROM waiting
                                      WHERE key = ?''', (key,))
                waiting_row = cur.fetchone()
                waiting_id = waiting_row['rowid']

                tags = []
                for row in conn.execute('SELECT tag FROM tags WHERE waiting_id = ?',
                                        str(waiting_id)):
                    tags.append(row['tag'])

                logger.info('Uploading photo %s for token %s', key, waiting_row['token'])

                flickr = flickrapi.FlickrAPI(options.api_key, options.api_secret, token=waiting_row['token'], store_token=False)

                try:
                    flickr.auth_checkToken()
                    flickr.upload(filename=datafile.name, title=str(waiting_row['title']), tags=str(' '.join(tags)))
                    logger.info('Uploading photo %s succeeded', key)
                except flickrapi.FlickrError:
                    logger.info('Uploading photo %s failed', key)

                conn.execute('DELETE FROM waiting WHERE rowid = ?', str(waiting_id))
                conn.execute('DELETE FROM tags WHERE waiting_id = ?', str(waiting_id))
                conn.commit()

                os.unlink(datafile.name)

        time.sleep(PAUSE_TIME)

if __name__ == '__main__':
    main()
