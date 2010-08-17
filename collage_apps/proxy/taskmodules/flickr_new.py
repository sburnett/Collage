# Low performance, more deniability. Decode censored content from Flickr by  searching for keywords.

import hashlib
import base64
from datetime import datetime, timedelta
import time

import pdb

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException

max_age = timedelta(3,)

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

                #try:
                #    uploaded_link = d.find_element_by_xpath('//a[@property="dc:date"]')
                #    uploaded_string = uploaded_link.get_text()
                #    uploaded_date = datetime.strptime(uploaded_string, '%B %d, %Y')
                #    print 'Photo uploaded on: %s' % (str(uploaded_date),)
                #    if datetime.now() - uploaded_date > max_age:
                #        return
                #except NoSuchElementException:
                #    pass

                try:
                    options_button = d.find_element_by_id('button-bar-options')
                except NoSuchElementException:
                    d.back()
                    continue

                try:
                    zoom_button = d.find_element_by_xpath('//div[@id="options-menu"]/ul/li/a[@data-ywa-name="All Sizes"]')
                    while not zoom_button.is_displayed():
                        options_button.click()
                        time.sleep(1)
                    zoom_button.click()
                except NoSuchElementException:
                    d.back()
                    continue

                ##################
                # Photo sizes page

                click_another_size = False

                # If we're not on the "original" size, then
                # try to click the "original" link, if it exists
                links = d.find_elements_by_xpath('//td/a')
                for link in links:
                    if link.get_text() == 'Original':
                        link.click()
                        click_another_size = True
                        break

                # Now check to see if we are in fact on the
                # "original" size. If we are, then download
                # the photo. Otherwise, go back to the previous page
                size_text = d.find_element_by_xpath('//td[@class="allsizes-selected"]')
                current_text = size_text.get_text().split()[0]
                if current_text == 'Original':
                    img = d.find_element_by_xpath('//div[@id="allsizes-photo"]/img')
                    src = img.get_attribute('src')

                    data = d.get_url_from_cache(src)
                    print hashlib.md5(data).hexdigest()
                    yield OutguessVector(data)

                if click_another_size:
                    d.back()   # Back to first size photo page
                    time.sleep(1)
                d.back()       # Back to photo summary page
                time.sleep(1)
                d.back()       # Back to search results page
                time.sleep(1)
        
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
