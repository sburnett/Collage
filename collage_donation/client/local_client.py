#!/usr/bin/env python

import os.path
import subprocess
import time
import sys
import base64
import hashlib
import glob

APPLICATION_NAME = 'proxy'

def find_filename(directory):
    idx = 0
    while os.path.exists(os.path.join(directory, '%s.jpg' % idx)):
        idx += 1
    return idx

def donate(directory, filename, id):
    handle = open(filename, 'r')
    submit_path = ['python', 'submit.py', APPLICATION_NAME, '--attribute=client:local', '--attribute=id:%s' % id]
    proc = subprocess.Popen(submit_path, stdin=handle, stdout=subprocess.PIPE)
    rc = proc.wait()
    key = proc.stdout.read()

    if key is None \
            or len(key) == 0 \
            or rc != 0:
        print 'Could not donate.'
        return

    print 'Processing donation...'

    poll_period = 1
    vdir = os.path.join(directory, id)
    if not os.path.exists(vdir):
        os.mkdir(vdir)
    idx = find_filename(vdir)
    while True:
        time.sleep(poll_period)

        filename = os.path.join(vdir, '%d.jpg' % idx)
        retrieve_path = ['python', 'retrieve.py', key]
        outfile = open(filename, 'w')
        proc = subprocess.Popen(retrieve_path, stdout=outfile)
        rc = proc.wait()
        outfile.close()
        if rc == 0:
            print 'Successfully donated photo'
            return

def main():
    usage = 'usage: %s <host directory> <source directory> <id>'
    if len(sys.argv) != 4:
        raise ValueError(usage)

    directory = sys.argv[1]
    source_dir = sys.argv[2]
    id = base64.b64encode(hashlib.sha1(sys.argv[3]).digest(), '-_')
    for filename in glob.glob(os.path.join(source_dir, '*.jpg')):
        donate(directory, filename, id)

if __name__ == '__main__':
    main()
