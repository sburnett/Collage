# Decode censored content from Flickr

import hashlib
import base64
import time
import tempfile
import os
import re

from collage.messagelayer import Task
from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException

import pdb

#max_age = timedelta(3,)

page_html = '<html><body><img src="%s"/></body></html>'

class WebTagsPicasaTask(Task):
    def __init__(self, driver, tags):
        self._driver = driver
        self._tags = tags

    def send(self, id, vector):
        raise NotImplementedError("Use photo donation tool")

    def receive(self, id):
        key = base64.b64encode(id)

        d = self._driver

        #########################
        # Main page

        d.get('http://picasaweb.google.com')

        search_field = d.find_element_by_id('sq')
        search_field.send_keys(' '.join(self._tags))
        search_button = d.find_element_by_xpath('//form/table/tbody/tr/td/font[@class="bodytext"]/input[@type="submit"]')
        search_button.click()

        #########################
        # Search results page

        # Toggle date ordering
        order_date = d.find_element_by_partial_link_text('Order by date')
        order_date.click()

        thumb_path = '(//a[@class="goog-icon-list-icon-link"])[%d]'

        pages_remaining = True
        while pages_remaining:
            for idx in range(25):
                d.wait_for_xpath('//a[@class="goog-icon-list-icon-link"]')

                try:
                    thumb = d.find_element_by_xpath(thumb_path % (idx+1))
                except NoSuchElementException:
                    break

                thumb.click()

                #######################
                # Photo page

                img = d.patient_find_element_by_xpath('//div[@class="scaledimage-onscreenpane"]/img')
                src = img.get_attribute('src')
                full_src = re.sub(r'/[^/]+/([^/]+)$', r'/d/\1', src)

                html_file = tempfile.NamedTemporaryFile(delete=False)
                html_file.write(page_html % full_src)
                html_file.close()

                # Load locally-hosted full-sized photo page
                d.get('file://%s' % html_file.name)
                try:
                    data = d.get_url_from_cache(full_src)
                    print hashlib.md5(data).hexdigest()
                    yield OutguessVector(data)
                except:
                    print 'Unable to fetch photo from cache'
                d.back()

                os.unlink(html_file.name)

                d.real_back()

            next_link = d.patient_find_element_by_xpath('//div[@class="pagernextnum"]')
            if len(next_link.get_text().strip()) > 0:
                next_link.click()
            else:
                pages_remaining = False

            next_link.click()   # On to the next results page

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

    def can_embed(self, id, data):
        return True
