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

class WebTagPairFlickrTask(Task):
    def __init__(self, driver, tags):
        self._driver = driver
        self._tags = tags

    def send(self, id, vector):
        raise NotImplementedError("Use photo donation tool")

    def receive(self, id):
        key = base64.b64encode(id)

        d = self._driver

        ###########
        # Main page
        
        d.get('http://www.flickr.com')

        search_field = d.find_element_by_xpath('//input[@name="q"]')
        search_field.send_keys(' '.join(self._tags))
        
        search_button = d.find_element_by_xpath('//form/input[@class="Butt"]')
        search_button.click()

        #####################
        # Search results page
        
        search_links = d.find_elements_by_partial_link_text('Advanced Search')
        if len(search_links) > 0:
            search_links[0].click()

        ######################
        # Advanced search page

        d.find_element_by_id('tagsonly').click()

        datemode = d.find_element_by_name('date_mode')
        datemode.click()
        datemode.send_keys('p')

        submit_button = d.find_element_by_xpath('//input[@class="Butt"]')
        submit_button.click()
        
        #####################
        # Search results page
        
        thumb_path = '(//img[@class="pc_img"])[%d]'

        pages_remaining = True
        while pages_remaining:
            thumbs_remaining = True
            idx = 0
            while thumbs_remaining:
                idx += 1

                try:
                    thumb = d.find_element_by_xpath(thumb_path % idx)
                except NoSuchElementException:
                    thumbs_remaining = False
                    continue

                thumb.click()

                ####################
                # Photo summary page

                try:
                    zoom_button = d.find_element_by_id('photo_gne_button_zoom')
                except NoSuchElementException:
                    d.back()
                    continue

                zoom_button.click()

                ##################
                # Photo sizes page

                click_another_size = False

                # If we're not on the "original" size, then
                # try to click the "original" link, if it exists
                strong_text = d.find_element_by_xpath('//td/strong')
                current_text = strong_text.get_text()
                if current_text != 'Original':
                    links = d.find_elements_by_xpath('//td/a')
                    for link in links:
                        if link.get_text() == 'Original':
                            link.click()
                            click_another_size = True
                    if not click_another_size:
                        links = d.find_elements_by_xpath('//td/a')
                        for link in links:
                            if link.get_text() == 'Large':
                                link.click()
                                click_another_size = True

                # Now check to see if we are in fact on the
                # "original" size. If we are, then download
                # the photo. Otherwise, go back to the previous page
                strong_text = d.find_element_by_xpath('//td/strong')
                current_text = strong_text.get_text()
                if current_text == 'Original' or \
                        current_text == 'Large':
                    img = d.find_element_by_xpath('//p/img')
                    src = img.get_attribute('src')

                    data = d.get_url_from_cache(src)
                    print hashlib.md5(data).hexdigest()
                    yield OutguessVector(data)

                if click_another_size:
                    d.back()   # Back to first size photo page
                d.back()       # Back to photo summary page
                d.back()       # Back to search results page
        
            try:
                next_link = d.find_element_by_xpath('//a[@class="Next"]')
            except NoSuchElementException:
                pages_remaining = False     # There are no results remaining
                continue

            next_link.click()   # On to the next results page

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

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
