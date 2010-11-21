"""Upload photos using Collage's donation system, to a local content host.

This is for testing only, and obviously can't be used in real applications.

"""

import base64
import hashlib

from collage.messagelayer import Task

class DonateDirectoryTask(Task):
    def __init__(self, directory, id, database):
        self._directory = directory
        self._db = database
        self._id = base64.b64encode(hashlib.sha1(id).digest(), '-_')

    def get_directory(self):
        return self._directory

    def send(self, id, vector):
        data = open(self._db.get_filename(vector.get_key()), 'wb')
        data.write(vector.get_data())
        data.flush()
        self._db.mark_done(vector.get_key())

    def receive(self, id):
        raise NotImplementedError('Use proxy client')

    def can_embed(self, id, data):
        return True

    def _hash(self):
        return hashlib.sha1(self._directory + self._id).digest()

    def get_attributes(self):
        return [('id', self._id)]
