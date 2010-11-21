import sys
import time

try:
    import wx
    from wx.lib.pubsub import Publisher
except ImportError:
    pass

import collage.instrument as instrument

class Timestamper(instrument.Instrument):
    """For each logging event, write a tiimestamped message to a logfile."""

    def stamp(self, ty, message):
        sys.stderr.write('%f %s %s\n' % (time.time(), ty, message))

    def change_status(self, status):
        self.stamp('status', status)

    def upload_vector(self, num_bytes):
        self.stamp('vector', num_bytes)

    def upload_chunks(self, num_bytes):
        self.stamp('chunks', num_bytes)

class Logger(instrument.Instrument):
    """For each logging event, post a wxPython event.

    Used in wxPython applications, like our proxy client.

    """

    def __init__(self, queue):
        self._queue = queue

    def put_message(self, ty, msg):
        try:
            self._queue.put((ty, msg), False)
        except Full:
            pass

    def change_status(self, status):
        wx.CallAfter(Publisher().sendMessage, 'status', status)

    def process_chunks(self, num_bytes):
        wx.CallAfter(Publisher().sendMessage, 'chunk', num_bytes)

    def process_vector(self, num_bytes):
        wx.CallAfter(Publisher().sendMessage, 'vector', num_bytes)
