import base64
import tempfile
import urllib
import hashlib

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

class DirectFlickrTask(Task):
    def __init__(self, flickr):
        self._flickr = flickr

    def upload_progress(self, progress, done):
        if done:
            print 'Done uploading'
        else:
            print '%d%% done' % progress

    def send(self, id, vector):
        photo = tempfile.NamedTemporaryFile(suffix='.jpg')
        photo.write(vector.get_data())
        photo.flush()
        title = base64.b64encode(id)

        self._flickr.upload(filename=photo.name, title=title,
                            description='', tags='', callback=self.upload_progress)

    def receive(self, id):
        key = base64.b64encode(id)
        results = self._flickr.photos_search(user_id='me', extras='url_o')

        for photo in results[0]:
            if 'title' in photo.attrib and photo.attrib['title'] == key:
                try:
                    data = urllib.urlopen(photo.attrib['url_o']).read()
                    yield OutguessVector(data)
                except Exception as e:
                    print e.message

    def can_embed(self, id, data):
        return True

class TagPairFlickrTask(Task):
    def __init__(self, flickr, tags):
        self._flickr = flickr
        self._tags = tags

    def upload_progress(self, progress, done):
        if done:
            print 'Done uploading'
        else:
            print '%d%% done' % progress

    def send(self, id, vector):
        photo = tempfile.NamedTemporaryFile(suffix='.jpg')
        photo.write(vector.get_data())
        photo.flush()
        title = base64.b64encode(id)

        self._flickr.upload(filename=photo.name, title=title,
                            description='', tags=' '.join(self._tags),
                            callback=self.upload_progress)

    def receive(self, id):
        key = base64.b64encode(id)
        # By default, search top 100 photos
        results = self._flickr.photos_search(extras='url_o', tags=','.join(self._tags), tag_mode='any')

        for photo in results[0]:
            if 'title' in photo.attrib and photo.attrib['title'] == key:
                try:
                    data = urllib.urlopen(photo.attrib['url_o']).read()
                    yield OutguessVector(data)
                except Exception as e:
                    print e.message

    def can_embed(self, id, data):
        return True

class DonateTagPairFlickrTask(Task):
    def __init__(self, tags, database):
        self._tags = tags
        self._db = database

    def get_tags(self):
        return self._tags

    def send(self, id, vector):
        photo = open(self._db.get_filename(vector.get_key()), 'wb')
        photo.write(vector.get_data())
        photo.flush()
        self._db.mark_done(vector.get_key())

    def receive(self, id):
        raise NotImplementedError('Use proxy client')

    def can_embed(self, id, data):
        return True

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

    def get_attributes(self):
        return map(lambda t: ('tag', t), self._tags)

