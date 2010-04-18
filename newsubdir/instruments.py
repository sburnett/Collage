import sys
import time
from Queue import Full

def timestamper(message):
    sys.stderr.write('%f %s\n' % (time.time(), message))

def create_logger(log_queue):
    def logger(message):
        try:
            log_queue.put(message, False)
        except Full:
            pass
    return logger
