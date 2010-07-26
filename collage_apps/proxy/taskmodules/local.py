# Test module that "downloads" images from local directory

import hashlib
import base64
import glob
import os.path

import pdb

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException

import pdb

class ReadDirectory(Task):
    def __init__(self, directory):
        self._directory = directory

    def send(self, id, vector):
        raise NotImplementedError("Use photo donation tool")

    def receive(self, id):
        pdb.set_trace()

        key = base64.b64encode(id, '-_')
        directory = os.path.join(self._directory, key)

        for filename in glob.iglob(os.path.join(directory, '*.jpg')):
            data = open(os.path.join(directory, filename), 'r').read()
            yield OutguessVector(data)

    def _hash(self):
        return hashlib.sha1(' '.join(self._directory)).digest()

    def can_embed(self, id, data):
        return True
