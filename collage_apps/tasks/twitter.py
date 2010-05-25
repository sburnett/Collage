import time
import random

from collage.messagelayer import Task

from selenium.common.exceptions import NoSuchElementException

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
