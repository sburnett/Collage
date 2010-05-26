#!/usr/bin/env python

# Suggested usage:
#
# flickr_upload_daemon.py -a client:web vectors
#
# (Ensure that directory vectors exists.) This will upload all
# photos that we donated by the Web donation client.

from optparse import OptionParser
import time
import os
import sqlite3
import tempfile

import flickrapi

from collage_donation.client.rpc import retrieve

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

DONATION_SERVER = 'http://127.0.0.1:8000'
PAUSE_TIME = 3

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='waiting_keys.sqlite3')
    parser.add_option('-d', '--database', dest='database', action='store', type='string', help='Waiting keys database')
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.error('Invalid argument')

    conn = sqlite3.connect(options.database)
    conn.row_factory = sqlite3.Row
    conn.execute('''CREATE TABLE IF NOT EXISTS waiting
                    (key TEXT, title TEXT, token TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS tags
                    (tag TEXT, waiting_id INTEGER)''')
    
    while True:
        keys = []
        cur = conn.execute('SELECT key FROM waiting')
        for row in cur:
            keys.append(row['key'])

        for key in keys:
            data = retrieve(DONATION_SERVER, key)
            if data != '':
                datafile = tempfile.NamedTemporaryFile(delete=False)
                datafile.write(data)
                datafile.close()

                cur = conn.execute('''SELECT rowid,* FROM waiting
                                      WHERE key = ?''', (key,))
                waiting_row = cur.fetchone()
                waiting_id = waiting_row['rowid']

                tags = []
                for row in conn.execute('SELECT tag FROM tags WHERE waiting_id = ?',
                                        waiting_id):
                    tags.append(row['tag'])

                flickr = flickrapi.FlickrAPI(api_key, api_secret, token=row['token'], store_token=False)
                
                try:
                    flickr.auth_checkToken()
                    flickr.upload(filename=datafile.name, title=str(row['title']), tags=str(' '.join(tags)))
                except flickrapi.FlickrError:
                    pass

                conn.execute('DELETE FROM waiting WHERE rowid = ?', waiting_id)
                conn.execute('DELETE FROM tags WHERE waiting_id = ?', waiting_id)
                conn.commit()

                os.unlink(datafile.name)

        time.sleep(PAUSE_TIME)

if __name__ == '__main__':
    main()
