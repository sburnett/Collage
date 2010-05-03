#!/usr/bin/env python

import os.path
import subprocess
import time

APPLICAITON_NAME = 'proxy'

def find_filename(directory):
    idx = 0
    while os.path.exists(os.path.join(directory, '%s.jpg' % idx)):
        idx += 1
    return idx

def donate(directory, filename):
    handle = open(filename, 'r')
    submit_path = ['python', 'submit.py', APPLICAITON_NAME, '--attribute=client:dummy']
    proc = subprocess.Popen(submit_path, stdin=handle, stdout=subprocess.PIPE)
    rc = proc.wait()
    key = proc.stdout.read()

    if key is None \
            or len(key) == 0 \
            or rc != 0:
        print 'Could not donate.'

    print 'Processing donation...'

    poll_period = 1
    vdir = os.path.join(directory, key)
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
            return

def main():
    usage = 'usage: %s <directory> <photo>'
    if len(sys.argv) != 3:
        raise ValueError(usage)

    directory = sys.argv[1]
    filename = sys.argv[2]

    donate(directory, filename)

if __name__ == '__main__':
    main()
