#!/usr/bin/env python
"""A daemon for donating a directory of photos once per day.

The photos are uploaded to a Flickr account, which must be authorized on the
first invocation of the program. (Credentials are cached in the user's home
directory.)

Important: Photos will be tagged with some provided tags. All photos with those
tags will be erased before uploading, so this could erase some photos
unintentionally.

After all the photos are uploaded, the program will sleep for 24 hours, then
repeat the process.

"""

import os.path
import os
import subprocess
import time
import sys
import base64
import glob
from optparse import OptionParser
import tempfile
import datetime

import flickrapi
import Image

from collage_apps.proxy.proxy_common import format_address

try:
    from collage_vis.database import get_database
except ImportError:
    get_database = None

APPLICATION_NAME = 'proxy_centralized'

def upload_progress(progress, done):
    if done:
        print 'Done uploading'
    else:
        print 'Uploading %d%% done' % progress

def upload_photo(flickr, filename, title, description, tags):
    flickr.upload(filename=filename, title=title, description=description, tags=tags, callback=upload_progress)

def delete_photos(flickr, tags):
    """Delete all my photos with these tags."""
    for photo in flickr.walk(tag_mode='all', tags=','.join(tags), user_id='me'):
        flickr.photos_delete(photo_id=photo.get('id'))

def need_to_upload(flickr, tags):
    """Don't upload if photos with these tags were uploaded in the past day."""
    today = datetime.datetime.utcnow()
    out_of_date = False
    found_photo = False
    for photo in flickr.walk(tag_mode='all', tags=','.join(tags), user_id='me', extras='date_upload'):
        found_photo = True
        timestamp = datetime.datetime.fromtimestamp(int(photo.get('dateupload')))
        if timestamp.day != today.day:
            out_of_date = True
    return (not found_photo) or out_of_date

def donate(flickr, filename, id, title, tags, db=None):
    if db is not None:
        db.embed_photo(filename)

    handle = open(filename, 'r')
    submit_path = [sys.executable, '-m', 'collage_donation.client.submit', APPLICATION_NAME, '--attribute=client:centralized', '--attribute=id:%s' % id]
    submit_path.extend(map(lambda tag: '--attribute=tag:%s' % tag, tags))
    proc = subprocess.Popen(submit_path, stdin=handle, stdout=subprocess.PIPE)
    rc = proc.wait()
    key = proc.stdout.read()

    print 'Wating for key %s' % key

    if key is None \
            or len(key) == 0 \
            or rc != 0:
        print 'Could not donate.'
        if db is not None:
            db.remove_photo(filename)
        return

    print 'Processing donation...'

    poll_period = 1
    while True:
        time.sleep(poll_period)

        retrieve_path = [sys.executable, '-m', 'collage_donation.client.retrieve', key]
        outfile = tempfile.NamedTemporaryFile(delete=False)
        proc = subprocess.Popen(retrieve_path, stdout=outfile)
        rc = proc.wait()
        outfile.close()

        if rc == 0:
            try:
                upload_photo(flickr, outfile.name, title, '', tags)
            except:
                print 'Failed to donate photo'
                if db is not None:
                    db.remove_photo(filename)
                return

            print 'Successfully donated photo'
            if db is not None:
                db.upload_photo(filename)
            return

def auth_flickr():
    """Authenticate with Flickr using our api key and secret.

    The user will be prompted to authenticate using his account if needed. If
    you want crediantials cached between sessions, make sure to run as the same
    user.
    
    """

    api_key = os.environ['CENTRALIZED_FLICKR_API_KEY']
    api_secret = os.environ['CENTRALIZED_FLICKR_SECRET']

    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='delete')
    if not token:
        raw_input('Press ENTER after you have authorized this program')
    flickr.get_token_part_two((token, frob))
    return flickr

def main():
    usage = 'usage: %s <photos directory>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(always=False)
    parser.add_option('-a', '--always-upload', dest='always',
                      action='store_true',
                      help="Don't check if photos have already been uploaded")
    options, args = parser.parse_args()

    if len(args) != 1:
        parser.error('Must specify photos directory')

    directory = args[0]
    title = 'Yellowstone photos'
    tags = ['nature', 'vacation']

    flickr = auth_flickr()

    if get_database is not None:
        vis_database = get_database()
    else:
        vis_database = None

    while True:
        today = datetime.datetime.utcnow()

        if options.always or need_to_upload(flickr, tags):
            delete_photos(flickr, tags)

            if vis_database is not None:
                filenames = glob.glob(os.path.join(directory, '*.jpg'))
                for filename in filenames:
                    img = Image.open(filename)
                    img.thumbnail((128, 64), Image.ANTIALIAS)
                    outfile = StringIO.StringIO()
                    img.save(outfile, 'JPEG')
                    vis_database.enqueue_photo(filename, base64.b64encode(outfile.getvalue()))

            address = base64.b64encode(format_address(today))
            for filename in glob.glob(os.path.join(directory, '*.jpg')):
                donate(flickr, filename, address, title, tags, vis_database)

        while today.day == datetime.datetime.utcnow().day:
            time.sleep(1)

if __name__ == '__main__':
    main()
