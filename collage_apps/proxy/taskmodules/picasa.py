# Decode censored content from Flickr

import hashlib
import base64
from datetime import datetime, timedelta

from collage.messagelayer import Task

from collage_apps.vectors.jpeg import OutguessVector

from selenium.common.exceptions import NoSuchElementException

max_age = timedelta(3,)

class WebTagsPicasaTask(Task):
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
        
        d.get('http://picasaweb.google.com')

        search_field = d.find_element_by_id('sq')
        search_field.send_keys(' '.join(self._tags))
        
        search_button = d.find_element_by_xpath('//form/table/tbody/tr/td/font[@class="bodytext"]/input[@type="submit"]')
        search_button.click()

        #####################
        # Search results page

        # Toggle date ordering
        options_toggle = d.find_element_by_id(":7")
        options_toggle.click()

        order_date = d.find_element_by_partial_link_text('Order by date')
        order_date.click()
        
        search_links = d.find_elements_by_partial_link_text('Advanced Search')
        if len(search_links) > 0:
            search_links[0].click()

        #####################
        # Search results page
        
        thumb_path = '(//img[@class="goog-icon-list-icon-img"])[%d]'

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

                download_menu = d.find_element_by_xpath('//div[@class="goog-inline-block-lhcl_toolbar_text][2]')
                try:
                    uploaded_link = d.find_element_by_xpath('//a[@property="dc:date"]')
                    uploaded_string = uploaded_link.get_text()
                    uploaded_date = datetime.strptime(uploaded_string, '%B %d, %Y')
                    print 'Photo uploaded on: %s' % (str(uploaded_date),)
                    if datetime.now() - uploaded_date > max_age:
                        return
                except NoSuchElementException:
                    pass

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
                next_link = d.find_element_by_xpath('//div[@class="pagernextnum"]')
            except NoSuchElementException:
                pages_remaining = False     # There are no results remaining
                continue

            next_link.click()   # On to the next results page

    def _hash(self):
        return hashlib.sha1(' '.join(self._tags)).digest()

    def can_embed(self, id, data):
        return True
