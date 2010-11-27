# High performance, low deniability. Decode censored content from Flickr by searching a user's account

import hashlib
import base64
from datetime import datetime, timedelta
import time
import logging

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException

import pdb

max_age = timedelta(3,)

class FlickrTaskException(Exception):
    pass

class WebUserFlickrTask(Task):
    def __init__(self, driver, user):
        self._driver = driver
        self._user = user
        self._logger = logging.getLogger('collage_proxy')

    def send(self, id, vector):
        raise NotImplementedError("Use photo donation tool")

    def receive(self, id):
        key = base64.b64encode(id)

        d = self._driver

        ###########
        # Main page

        self._logger.info('Fetching Flickr main page')
        d.get('http://www.flickr.com')
        self._logger.info('On page: %s' % d.get_current_url())

        try:
            self._logger.info('Looking for search field')
            search_field = d.find_element_by_xpath('//input[@name="q"]')
        except:
            raise FlickrTaskException('Could not find search field')

        try:
            self._logger.info('Typing username "%s" in search field' % self._user)
            search_field.send_keys(self._user)
        except:
            raise FlickrTaskException('Could not type username in search field')

        try:
            self._logger.info('Clicking search button')
            search_button = d.find_element_by_xpath('//form/input[@class="Butt"]')
            search_button.click()
            self._logger.info('On page: %s' % d.get_current_url())
        except:
            raise FlickrTaskException('Could not click search button')

        #####################
        # Search results page

        try:
            self._logger.info('Finding "People" link')
            people_link = d.find_elements_by_partial_link_text('People')
        except:
            raise FlickrTaskException('Could not activate username search')

        try:
            self._logger.info('Clicking "People" link')
            people_link[0].click()
            self._logger.info('On page: %s' % d.get_current_url())
        except:
            raise FlickrTaskException('Could not activate username search')

        ######################
        # Advanced search page

        try:
            self._logger.info('Finding username "%s" on "People" search results page' % self._user)
            profile_link = d.find_elements_by_partial_link_text(self._user)
        except:
            raise FlickrTaskException('Could find username "%s" in search results' % self._user)
        try:
            self._logger.info('Clicking username "%s" in search results' % self._user)
            profile_link[0].click()
            self._logger.info('On page: %s' % d.get_current_url())
        except:
            raise FlickrTaskException('Could click username "%s" in search results' % self._user)

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
                    self._logger.info('Finding thumbnail %d using query %s' % (idx, thumb_path))
                    thumb = d.find_element_by_xpath(thumb_path % idx)
                except NoSuchElementException:
                    thumbs_remaining = False
                    continue

                self._logger.info('Clicking thumbnail %d' % idx)
                thumb.click()
                self._logger.info('On page: %s' % d.get_current_url())

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
                    self._logger.info('Finding "options" button')
                    options_button = d.find_element_by_id('button-bar-options')
                except NoSuchElementException:
                    self._logger.info('Could not find "options" button')
                    d.back()
                    continue

                try:
                    self._logger.info('Finding "zoom" button')
                    zoom_button = d.find_element_by_xpath('//div[@id="options-menu"]/ul/li/a[@data-ywa-name="All Sizes"]')
                    while not zoom_button.is_displayed():
                        self._logger.info('Clicking "options" button again')
                        options_button.click()
                        time.sleep(1)
                    self._logger.info('Clicking "zoom" button')
                    zoom_button.click()
                    self._logger.info('On page: %s' % d.get_current_url())
                except NoSuchElementException:
                    self._logger.info('Could not click "zoom" button')
                    d.back()
                    continue

                ##################
                # Photo sizes page

                click_another_size = False

                # If we're not on the "original" size, then
                # try to click the "original" link, if it exists
                self._logger.info('Finding photo size links')
                links = d.find_elements_by_xpath('//td/a')
                for link in links:
                    if link.get_text() == 'Original':
                        self._logger.info('Clicking "Original" size link')
                        link.click()
                        self._logger.info('On page: %s' % d.get_current_url())
                        click_another_size = True
                        break

                # Now check to see if we are in fact on the
                # "original" size. If we are, then download
                # the photo. Otherwise, go back to the previous page
                self._logger.info('Getting photo size text')
                size_text = d.find_element_by_xpath('//td[@class="allsizes-selected"]')
                current_text = size_text.get_text().split()[0]
                self._logger.info('Photo size is "%s"' % current_text)
                if current_text == 'Original':
                    self._logger.info('Getting photo URL')
                    img = d.find_element_by_xpath('//div[@id="allsizes-photo"]/img')
                    src = img.get_attribute('src')
                    self._logger.info('Photo URL is %s' % src)

                    data = d.get_url_from_cache(src)
                    self._logger.info('Got photo, has MD5 hash %s' % hashlib.md5(data).hexdigest())
                    yield OutguessVector(data, logger=self._logger)

                if click_another_size:
                    self._logger.info('Going back to first photo size page')
                    d.back()   # Back to first size photo page
                    self._logger.info('On page: %s' % d.get_current_url())
                    time.sleep(1)
                self._logger.info('Going back to photo summary page')
                d.back()       # Back to photo summary page
                self._logger.info('On page: %s' % d.get_current_url())
                time.sleep(1)
                self._logger.info('Going back to photo search results page')
                d.back()       # Back to search results page
                self._logger.info('On page: %s' % d.get_current_url())
                time.sleep(1)

            try:
                self._logger.info('Finding next link')
                next_link = d.find_element_by_xpath('//a[@class="Next"]')
            except NoSuchElementException:
                self._logger.info('No photo pages are remaining')
                pages_remaining = False     # There are no results remaining
                continue

            self._logger.info('Clicking "next" link for more search results')
            next_link.click()   # On to the next results page
            self._logger.info('On page: %s' % d.get_current_url())

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

    def can_embed(self, id, data):
        return True
