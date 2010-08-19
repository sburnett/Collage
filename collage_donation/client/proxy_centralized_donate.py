#!/usr/bin/env python

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

import pdb

import flickrapi

from collage_apps.proxy.proxy_common import format_address

APPLICATION_NAME = 'proxy_centralized'

def upload_progress(progress, done):
    if done:
        print 'Done uploading'
    else:
        print 'Uploading %d%% done' % progress

def upload_photo(flickr, filename, title, description, tags):
    flickr.upload(filename=filename, title=title, description=description, tags=tags, callback=upload_progress)

def delete_photos(flickr, tags):
    for photo in flickr.walk(tag_mode='all', tags=','.join(tags), user_id='me'):
        flickr.photos_delete(photo_id=photo.get('id'))

def need_to_upload(flickr, tags):
    today = datetime.datetime.utcnow()
    out_of_date = False
    found_photo = False
    for photo in flickr.walk(tag_mode='all', tags=','.join(tags), user_id='me', extras='date_upload'):
        found_photo = True
        timestamp = datetime.datetime.fromtimestamp(int(photo.get('dateupload')))
        if timestamp.day != today.day:
            out_of_date = True
    return (not found_photo) or out_of_date

def donate(flickr, filename, id, title, tags):
    handle = open(filename, 'r')
    submit_path = ['python', '-m', 'collage_donation.client.submit', APPLICATION_NAME, '--attribute=client:centralized', '--attribute=id:%s' % id]
    submit_path.extend(map(lambda tag: '--attribute=tag:%s' % tag, tags))
    proc = subprocess.Popen(submit_path, stdin=handle, stdout=subprocess.PIPE)
    rc = proc.wait()
    key = proc.stdout.read()

    print 'Wating for key %s' % key

    if key is None \
            or len(key) == 0 \
            or rc != 0:
        print 'Could not donate.'
        return

    print 'Processing donation...'

    poll_period = 1
    while True:
        time.sleep(poll_period)

        retrieve_path = ['python', '-m', 'collage_donation.client.retrieve', key]
        outfile = tempfile.NamedTemporaryFile(delete=False)
        proc = subprocess.Popen(retrieve_path, stdout=outfile)
        rc = proc.wait()
        outfile.close()

        if rc == 0:
            upload_photo(flickr, outfile.name, title, '', tags)
            print 'Successfully donated photo'
            return

def auth_flickr():
    """Authenticate with Flickr using our api key and secret.

    The user will be prompted to authenticate using his
    account if needed."""

    api_key = '3219bff0c8e25adc61ca3845f1c810c5'
    api_secret = '7ed8aaed85fa15c6'

    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    (token, frob) = flickr.get_token_part_one(perms='delete')
    if not token:
        raw_input('Press ENTER after you have authorized this program')
    flickr.get_token_part_two((token, frob))
    return flickr

def main():
    usage = 'usage: %s <photos directory>'
    if len(sys.argv) != 2:
        raise ValueError(usage)

    directory = sys.argv[1]
    title = 'Yellowstone photos'
    tags = ['nature', 'vacation']

    flickr = auth_flickr()

    while True:
        today = datetime.datetime.utcnow()

        if need_to_upload(flickr, tags):
            delete_photos(flickr, tags)

            address = base64.b64encode(format_address(today))
            for filename in glob.glob(os.path.join(directory, '*.jpg')):
                donate(flickr, filename, address, title, tags)

        while today.day == datetime.datetime.utcnow().day:
            time.sleep(1)

if __name__ == '__main__':
    main()
