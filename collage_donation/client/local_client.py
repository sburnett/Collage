#!/usr/bin/env python

import os.path
import subprocess
import time
import sys
import base64
import hashlib
import glob
import StringIO

import Image

try:
    from collage_vis.database import get_database
except ImportError:
    get_database = None

APPLICATION_NAME = 'proxy_local'

def find_filename(directory):
    idx = 0
    while os.path.exists(os.path.join(directory, '%s.jpg' % idx)):
        idx += 1
    return idx

def donate(directory, filename, id, db=None):
    if db is not None:
        db.embed_photo(filename)

    handle = open(filename, 'r')
    submit_path = [sys.executable, '-m', 'collage_donation.client.submit', APPLICATION_NAME, '--attribute=client:local', '--attribute=id:%s' % id]
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
    vdir = os.path.join(directory, id)
    if not os.path.exists(vdir):
        os.mkdir(vdir)
    idx = find_filename(vdir)
    while True:
        time.sleep(poll_period)

        hosted_filename = os.path.join(vdir, '%d.jpg' % idx)
        retrieve_path = [sys.executable, '-m', 'collage_donation.client.retrieve', key]
        outfile = open(hosted_filename, 'w')
        proc = subprocess.Popen(retrieve_path, stdout=outfile)
        rc = proc.wait()
        outfile.close()
        if rc == 0:
            if db is not None:
                db.upload_photo(filename)
            print 'Successfully donated photo'
            return

def main():
    usage = 'usage: %s <host directory> <source directory> <id>'
    if len(sys.argv) != 4:
        raise ValueError(usage)

    directory = sys.argv[1]
    source_dir = sys.argv[2]
    id = base64.b64encode(hashlib.sha1(sys.argv[3]).digest(), '-_')

    if get_database is not None:
        vis_database = get_database()
    else:
        vis_database = None

    if vis_database is not None:
        filenames = glob.glob(os.path.join(source_dir, '*.jpg'))
        for filename in filenames:
            img = Image.open(filename)
            img.thumbnail((128, 64), Image.ANTIALIAS)
            outfile = StringIO.StringIO()
            img.save(outfile, 'JPEG')
            vis_database.enqueue_photo(filename, base64.b64encode(outfile.getvalue()))

    for filename in glob.glob(os.path.join(source_dir, '*.jpg')):
        donate(directory, filename, id, vis_database)

if __name__ == '__main__':
    main()
