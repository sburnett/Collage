#!/usr/bin/env python

import cherrypy
from Cheetah.Template import Template
import flickrapi
import urllib
import re
import sys
import os
import StringIO
import sqlite3
import tempfile
from optparse import OptionParser

import Image

from collage_donation.client.rpc import submit, update_attributes

import pdb

script_path = os.path.dirname(sys.argv[0])
def template_path(name):
    return os.path.join(script_path, 'views', '%s.tpl' % name)

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

flickr = flickrapi.FlickrAPI(api_key, api_secret, store_token=False)

DONATION_SERVER = 'https://127.0.0.1:8000/server.py'
APPLICATION_NAME = 'proxy'
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
UPLOADS_DIR = os.path.abspath('uploads')

def get_latest_tags():
    pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
    match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
    block = match.group(1)
    print os.path.abspath(os.path.curdir)
    of = open('tags.tpl', 'w')
    matches = re.finditer(r'<a href=".*?" style="font-size: (?P<size>\d+)px;">(?P<tag>.*?)</a>', block)
    for (idx, match) in enumerate(matches):
        print >>of, '(new YAHOO.widget.Button({ type: "checkbox", label: "%s", id: "check%d", name: "check%d", value: "%s", container: "tagsbox"})).setStyle("font-size", "%spx");' % (match.group('tag'), idx, idx, match.group('tag'), match.group('size'))
    print >>of, 'document.write("<input type=\'hidden\' name=\'numtags\' value=\'%d\'/>");' % (idx+1)
    of.close()

class FlickrWebClient:
    def check_credentials(self):
        if 'token' not in cherrypy.session or \
                'userid' not in cherrypy.session:
            raise cherrypy.HTTPRedirect('/login')

        token = cherrypy.session['token']
        f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
        try:
            f.auth_checkToken()
        except flickrapi.FlickrError:
            raise cherrypy.HTTPRedirect('/login')

    def wait_for_key(key, title, token, tags):
        conn = sqlite3.connect(wait_db)
        cur = conn.execute('''INSERT INTO waiting (key, title, token)
                                           VALUES (?, ?, ?)''',
                           (key, title, token))
        rowid = cur.lastrowid
        for tag in tags:
            conn.execute('INSERT INTO tags (tag, waiting_id) VALUES (?, ?)', (tag, rowid))
        conn.commit()
        conn.close()

    @cherrypy.expose
    def index(self):
        self.check_credentials()
        raise cherrypy.HTTPRedirect('/upload')

    @cherrypy.expose
    def login(self):
        template = Template(file=template_path('login'))
        template.login_url=flickr.web_login_url(perms='write')
        return str(template)

    @cherrypy.expose
    def logout(self):
        del cherrypy.session['token']
        del cherrypy.session['userid']
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def upload(self, submit=None, title=None, vector_ids=None, numtags=None, expiration=None, **kwargs):
        self.check_credentials()

        template = Template(file=template_path('upload'))
        template.token = cherrypy.session['token']
        template.userid = cherrypy.session['userid']

        if submit is None:
            return str(template)
        
        title = title.strip()
        filenames = vector_ids.split(';')
        for filename in filenames:
            if len(filename) == 0 \
                    or not os.samefile(UPLOADS_DIR, os.path.dirname(filename)) \
                    or not os.path.exists(filename):
                template.error = 'You must select photos to upload'
                return str(template)

        try:
            numtags = int(numtags.strip())
        except ValueError:
            template.error = 'Inconsistent upload state. Please try again.'
            return str(template)

        numtags = max(numtags, 200)     # Hard clamp on the number of tags, to prevent DoS
        tags = []
        for idx in range(numtags):
            name = 'check%d' % idx
            if name in kwargs:
                tags.append(kwargs[name])
        if len(tags) < 3:
            template.error = 'Please select at least 3 tags from the list'
            return str(template)

        try:
            expiration = 60*60*int(expiration).strip()
        except ValueError:
            template.error = 'Please enter a valid number of hours'
            return str(template)
        attributes = map(lambda tag: ('tag', tag), tags)

        for filename in filenames:
            try:
                vector = open(filename, 'rb').read()
                os.unlink(filename)
                key = submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)
            except Exception as e:
                template.error = 'Cannot contact upload server. Please try again later.'
                return str(template)

            wait_for_key(key, title, token, tags)

        template = Template(file=template_path('process'))
        template.token = cherrypy.session['token']
        template.userid = cherrypy.session['userid']
        template.expiration = expiration/(60*60)
        return str(template)

    @cherrypy.expose
    def upload_file(self, vector=None, token=None, userid=None):
        pdb.set_trace()

        if vector is None or token is None or userid is None:
            raise cherrypy.HTTPError(403)

        f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
        try:
            f.auth_checkToken()
        except flickrapi.FlickrError:
            raise cherrypy.HTTPError(403)

        response = flickr.people_getInfo(user_id=userid)
        ispro = response.find('person').attrib['ispro'] == '1'

        data = vector.file.read()

        if ispro:
            vector = data
        else:
            img = Image.open(StringIO.StringIO(data))
            (width, height) = img.size
            ratio = min(1024./width, 768./height)
            if ratio >= 1.0:
                vector = data
            else:
                img = img.resize((int(ratio*width), int(ratio*height)), Image.ANTIALIAS)
                outfile = StringIO.StringIO()
                img.save(outfile, 'JPEG')
                vector = outfile.getvalue()
                outfile.close()

        outf = tempfile.NamedTemporaryFile(suffix='.jpg', prefix='upload', dir=UPLOADS_DIR, delete=False)
        outf.write(vector)
        outf.close()

        return outf.name

    @cherrypy.expose
    def callback(self, frob=None):
        token = flickr.get_token(frob)

        f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
        try:
            response = f.auth_checkToken()
        except flickrapi.FlickrError:
            raise cherrypy.HTTPRedirect('/login')

        userid = response.find('auth').find('user').attrib['nsid']

        print 'Updating: %s, %s' % (userid, token)

        update_attributes(DONATION_SERVER, 'userid', userid, 'token', token)

        cherrypy.session['token'] = token
        cherrypy.session['userid'] = userid
        raise cherrypy.HTTPRedirect('/')

def main():
    usage = 'usage: %s [options]'
    parser = OptionParser(usage=usage)
    parser.set_defaults(database='waiting_keys.sqlite')
    parser.add_option('-d', '--database', dest='database', action='store', type='string', help='Waiting keys database')
    (options, args) = parser.parse_args()

    global wait_db
    wait_db = options.database

    if len(args) != 0:
        parser.error('Invalid argument')

    get_latest_tags()
    
    cherrypy.config.update({'tools.sessions.on': True})
    config = { '/static':
                    { 'tools.staticdir.on' : True,
                      'tools.staticdir.dir': STATIC_DIR }
             }
    cherrypy.quickstart(FlickrWebClient(), config=config)

if __name__ == '__main__':
    main()
