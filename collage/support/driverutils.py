from taskdriver import task_driver

def load_url(url):
    snippet = 'DriverUtils.loadUrl(%s)' % repr(url)
    task_driver.run_snippet(snippet)

def get_url_from_cache(url):
    snippet = 'DriverUtils.getUrlFromCache(%s)' % repr(url)
    return task_driver.run_snippet(snippet)

def click_element_id(id):
    snippet = 'DriverUtils.getClickElementId(%s)' % repr(id)
    return task_driver.run_snippet(snippet)
