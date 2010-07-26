# Decode censored content from a simple content host

import hashlib
import base64
import urllib

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException

import pdb

class SimpleWebHostTask(Task):
    def __init__(self, driver, url):
        self._driver = driver
        self._url = url

    def send(self, id, vector):
        raise NotImplementedError("Use photo donation tool")

    def receive(self, id):
        id = base64.urlsafe_b64encode(id)
        d = self._driver

        pdb.set_trace()

        ###########
        # Main page
        
        d.get(self._url)

        links = d.find_elements_by_tag_name('a')
        for link in links:
            href = link.get_attribute('href')[1:]
            if urllib.unquote(href) == id:
                link.click()

                photo_links = d.find_elements_by_tag_name('a')
                for photo_link in photo_links:
                    photo_link.click()

                    img = d.find_element_by_tag_name('img')
                    src = img.get_attribute('src')
                    data = d.get_url_from_cache(self._url + src)
                    yield OutguessVector(data)

                    d.back()

                d.back()

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

    def can_embed(self, id, data):
        return True
