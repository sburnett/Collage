from taskdriver import task_driver

class ExecutionContext(object):
    def __init__(self):
        self.snippets = []

    def execute(self):
        result = task_driver.run_snippet(';'.join(self.snippets))
        self.snippets = []
        return result

    def execute_debug(self):
        for i in range(0, 2*len(self.snippets), 2):
            self.snippets[i:i] = ['\nprintln(%s)\n' % repr(self.snippets[i])]
        return self.execute()

    def add_snippet(self, snippet):
        self.snippets.append(snippet)

    def wait_for_load(self):
        self.add_snippet('DriverUtils.waitToLoad()')

    def prepare_for_page_change(self):
        self.add_snippet('DriverUtils.contentLoad = false')

    def load_url(self, url):
        self.add_snippet('DriverUtils.loadUrl(%s)' % repr(url))

    def get_url_from_cache(self, url):
        self.add_snippet('DriverUtils.getUrlFromCache(%s)' % repr(url))

    def click_element_id(self, id):
        self.add_snippet('DriverUtils.clickElementId(%s)' % repr(id))

    def type_element_id(self, id, s):
        for ch in s:
            self.add_snippet('DriverUtils.typeElementId(%s, %s)' % (repr(id), ord(ch)))

    def set_element_attribute(self, id, key, value):
        self.add_snippet('DriverUtils.setElementAttribute(%s, %s, %s)' % (repr(id), repr(key), repr(value)))

    def println(self, message):
        self.add_snippet('println(%s)' % repr(message))

    def quit(self):
        self.add_snippet('DriverUtils.closeWindow();')
