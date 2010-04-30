# Decode censored content from Flickr

import hashlib
import base64

from collage.messagelayer import Task

from vectors import OutguessVector

from selenium.common.exceptions import NoSuchElementException

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
