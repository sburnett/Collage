import base64
import tempfile
import urllib
import random
import os
import os.path
import time

from collage.messagelayer import Task
from collage.support.driverutils import ExecutionContext

from vectors import OutguessVector, SimulatedVector

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

    search_snippet = \
        '''
		DriverUtils.loadUrl("http://www.flickr.com");

		// Enter search terms into search box and click Search button
		var divSearch = DriverUtils.getElementById("featured-search");
		var inputFields = divSearch.getElementsByTagName("form")[0].getElementsByTagName("input");
		var textField = null, button = null;
		for(var k in inputFields) {
			if(inputFields[k].getAttribute("name") == "q")
				textField = inputFields[k];
			else if(inputFields[k].getAttribute("type") == "submit")
				button = inputFields[k];
		}

		textField.setAttribute("value", tags.join(" "));
		DriverUtils.clickElement(button);
        DriverUtils.waitToLoad();

		// Change from keyword search to tag search
		var tagsBox = DriverUtils.getElementById("mtags");
		clickElement(tagsBox);
		inputFields = DriverUtils.getElementsByTagName("input");
		for(var k in inputFields) {
			if(inputFields[k].getAttribute("type") == "submit"
					&& inputFields[k].getAttribute("class") == "Butt")
				button = inputFields[k];
		}
		DriverUtils.clickElement(button);

		// Now go through images on every page
		var resultBoxCounter = 0;
		while(true) {
			// Find next image result on this page.
			var resultBoxes = DriverUtils.getElementsByTagName("td");
			var k = 0;
			var rbc = -1;
			for(var l in resultBoxes)
				if(resultBoxes[l].getAttribute("class") != "DetailPic")
					continue;
				else {
					k++;
					if(k > resultBoxCounter) {
						rbc = l;
						break;
					}
				}

			if(rbc < 0) {
				// If we have visited all results, try to visit the next page.
				var links = DriverUtils.getElementsByTagName("a");
				var foundNext = false;
				for(var k in links)
					if(links[k].getAttribute("class") == "Next") {
						DriverUtils.clickElement(links[k]);
						foundNext = true;
						break;
					}

				if(!foundNext)
					break;
				else {
					resultBoxCounter = 0;
					continue;
				}
			}

			resultBoxCounter++;

			// Click the image
			var img = resultBoxes[rbc].getElementsByTagName("img")[0];
			DriverUtils.clickElement(img);
            DriverUtils.waitToLoad();

			// Click the Zoom button, if it is available
			var zoom = DriverUtils.getElementById("photo_gne_button_zoom");
			if(zoom != null) {
				DriverUtils.clickElement(zoom);
                DriverUtils.waitToLoad();

				// Click the "Original size" button if available
				var tds = DriverUtils.getElementsByTagName("td");
				var re = /Original/;
				var clickedFullSize = false;
				for(var l in tds) {
					var links = tds[l].getElementsByTagName("a");
					for(var m in links) {
						if(re.test(links[m].firstChild.nodeValue)) {
							DriverUtils.clickElement(links[m].firstChild);
							DriverUtils.waitToLoad();
							clickedFullSize = true;
						}

						if(clickedFullSize)
							break;
					}

					if(clickedFullSize)
						break;
				}

				// Now save the image from the cache.
				var imgs = DriverUtils.getElementsByTagName("img");
				for(var l in imgs) {
					if(imgs[l].nextSibling != null
							&& imgs[l].nextSibling.nodeName == "BR") {
						var imgData = DriverUtils.getFromCache(imgs[l].getAttribute("src"));
					}
				}

				DriverUtils.goBack();
				yield imgData;

				if(clickedFullSize) {
                    DriverUtils.goBack();
				}
			}

			frame.goBack();
        }
        '''

    def receive(self, id):
        key = base64.b64encode(id)

        ctx = ExecutionContext()
        ctx.load_url('http://www.flickr.com')
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
            time.sleep(tottime)

    def receive(self, id):
        msgs = []
        traffic = 0
        for i in range(self._vectors_per_task):
            files = filter(lambda f: os.path.splitext(f)[1] == '.vector', os.listdir(self._storage_dir))
            filename = random.choice(files)
            data = open(os.path.join(self._storage_dir, filename), 'r').read()
            traffic += len(data)
            yield SimulatedVector(data, 0.0)

        traffic += self._traffic_overhead
        tottime = traffic/self._download + random.gauss(self._time_overhead, self._time_deviation)
        time.sleep(tottime)

    def can_embed(self, id, data):
        return True
