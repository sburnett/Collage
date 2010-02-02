import sys
import time

def timestamper(message):
    sys.stderr.write('%f %s\n' % (time.time(), message))
