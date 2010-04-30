import base64
import tempfile
import urllib
import random
import os
import os.path
import time
import sys
import hashlib

from collage.messagelayer import Task

from vectors import OutguessVector, SimulatedVector

from selenium.common.exceptions import NoSuchElementException

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

class DirectTwitterTask(Task):
    def __init__(self, twitter, username, VectorClass):
        self._twitter = twitter
        self._username = username
        self._VectorClass = VectorClass

    def send(self, id, vector):
        self._twitter.PostUpdate(vector.get_data())

    def receive(self, id):
        results = self._twitter.GetUserTimeline(self._username)
        for status in results:
            yield self._VectorClass(status.text)

    def can_embed(self, id, data):
        return True

class WebTwitterTask(Task):
    def __init__(self, driver, username, VectorClass):
        self._driver = driver
        self._username = username
        self._VectorClass = VectorClass

    def send(self, id, vector):
        self._driver.find_element_by_id('status').send_keys(vector.get_data())
        self._driver.find_element_by_id('tweeting_button').click()
        pause = abs(random.gauss(10, 5))
        print 'Pausing for %d seconds' % pause
        time.sleep(pause)


    def receive(self, id):
        self._driver.get('http://www.twitter.com/%s' % self._username)
    
        num_processed = 0
        while True:
            statuses = self._driver.find_elements_by_xpath('(//ol[@id="timeline"]/li/span[@class="status-body"]/span[@class="status-content"]/span[@class="entry-content"])[position() > %d]' % num_processed)
            for status in statuses:
                yield self._VectorClass(status.get_text())
                num_processed += 1

            try:
                self._driver.find_element_by_id('more').click()
            except NoSuchElementException:
                return

    def can_embed(self, id, data):
        return True

class SimulatedTask(Task):
    def __init__(self, traffic_overhead,
                 time_overhead, time_deviation,
                 download, upload,
                 vectors_per_task,
                 storage_dir):
        self._traffic_overhead = traffic_overhead
        self._time_overhead = time_overhead
        self._time_deviation = time_deviation
        self._download = (download*1000)/8.
        self._upload = (upload*1000)/8.
        self._vectors_per_task = vectors_per_task
        self._storage_dir = storage_dir

    def send(self, id, vector):
        for i in range(self._vectors_per_task):
            filename = os.path.join(self._storage_dir, str(random.getrandbits(32)) + '.vector')
            open(filename, 'w').write(vector.get_data())
            traffic = len(vector.get_data()) + self._traffic_overhead
            tottime = traffic/self._upload + random.gauss(self._time_overhead, self._time_deviation)
            sys.stderr.write('%f %s\n' % (time.time(), 'send traffic %d time %d' % (traffic, tottime)))

    def receive(self, id):
        msgs = []
        for i in range(self._vectors_per_task):
            files = filter(lambda f: os.path.splitext(f)[1] == '.vector', os.listdir(self._storage_dir))
            filename = random.choice(files)
            data = open(os.path.join(self._storage_dir, filename), 'r').read()
            traffic = len(data) + self._traffic_overhead
            tottime = traffic/self._download + random.gauss(self._time_overhead, self._time_deviation)
            sys.stderr.write('%f %s\n' % (time.time(), 'receive traffic %d time %d' % (traffic, tottime)))
            yield SimulatedVector(data, 0.0)

    def can_embed(self, id, data):
        return True
