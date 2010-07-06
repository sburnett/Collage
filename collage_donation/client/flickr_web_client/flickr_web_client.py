#!/usr/bin/env python

from bottle import route, view
import bottle
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

bottle.debug(True)
bottle.TEMPLATE_PATH.append(os.path.join(script_path, 'views'))

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

flickr = flickrapi.FlickrAPI(api_key, api_secret, store_token=False)

DONATION_SERVER = 'https://127.0.0.1:8000/server.py'
APPLICATION_NAME = 'proxy'
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

def check_credentials():
    if 'token' not in bottle.request.COOKIES or \
            'userid' not in bottle.request.COOKIES:
        return False

    token = bottle.request.COOKIES['token']
    f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
    try:
        response = f.auth_checkToken()
    except flickrapi.FlickrError:
        return False

    return True

@route('/')
def index():
    if 'token' in bottle.request.COOKIES and \
            'userid' in bottle.request.COOKIES:
        bottle.redirect('/upload')
    else:
        bottle.redirect('/login')

@route('/static/:filename#.*#')
def send_static(filename):
    return bottle.send_file(filename, os.path.join(script_path, 'static'))

@route('/login')
@view('login')
def login():
    return dict(login_url=flickr.web_login_url(perms='write'))

@route('/logout')
def logout():
    bottle.response.set_cookie('token', '', path='/', expires=-3600)
    bottle.response.set_cookie('userid', '', path='/', expires=-3600)
    bottle.redirect('/')

@route('/upload')
@view('upload')
def upload():
    if not check_credentials():
        bottle.redirect('/login')
    token = bottle.request.COOKIES['token']
    userid = bottle.request.COOKIES['userid']
    return {'token': token, 'userid': userid}

@route('/upload', method='POST')
def process():
    if not check_credentials():
        bottle.redirect('/login')
    elif 'submit' not in bottle.request.POST:
        bottle.redirect('/upload')
    else:
        token = bottle.request.COOKIES['token']
        userid = bottle.request.COOKIES['userid']

        title = bottle.request.POST.get('title', '').strip()
        filenames = bottle.request.POST.get('vector_ids').split(';')
        for filename in filenames:
            if len(filename) == 0 \
                    or not os.samefile(UPLOADS_DIR, os.path.dirname(filename)) \
                    or not os.path.exists(filename):
                return bottle.template('upload', error='You must select photos to upload',
                                                 token=token, userid=userid)

        try:
            numtags = int(bottle.request.POST.get('numtags', '').strip())
        except ValueError:
            return bottle.template('upload', error='Inconsistent upload state. Please try again.',
                                             token=token, userid=userid)
        numtags = max(numtags, 200)     # Hard clamp on the number of tags, to prevent DoS
        tags = []
        for idx in range(numtags):
            name = 'check%d' % idx
            if name in bottle.request.POST:
                tags.append(bottle.request.POST[name])
        if len(tags) < 3:
            return bottle.template('upload', error='Please select at least 3 tags from the list',
                                             token=token, userid=userid)
        try:
            expiration = 60*60*int(bottle.request.POST.get('expiration', '').strip())
        except ValueError:
            return bottle.template('upload', error='Please enter a valid number of hours',
                                             token=token, userid=userid)
        attributes = map(lambda tag: ('tag', tag), tags)

        for filename in filenames:
            try:
                vector = open(filename, 'rb').read()
                os.unlink(filename)
                key = submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)
            except Exception as e:
                print 'Error: %s' % e
                return bottle.template('upload', error='Cannot contact upload server. Please try again later.',
                                                 token=token, userid=userid)

            wait_for_key(key, title, token, tags)

        return bottle.template('process', expiration=expiration/(60*60))

@route('/upload_file', method='POST')
def upload_file():
    token = bottle.request.POST.get('token')
    userid = bottle.request.POST.get('userid')
    uploaded = bottle.request.POST.get('vector')
    data = uploaded.file.read()

    if not token or not userid:
        bottle.redirect('/login')
        return

    f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
    try:
        response = f.auth_checkToken()
    except flickrapi.FlickrError:
        bottle.redirect('/login')
        return

    response = flickr.people_getInfo(user_id=userid)
    ispro = response.find('person').attrib['ispro'] == '1'

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

@route('/callback')
def callback():
    frob = bottle.request.GET['frob']
    token = flickr.get_token(frob)

    f = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
    try:
        response = f.auth_checkToken()
    except flickrapi.FlickrError:
        bottle.redirect('/login')

    userid = response.find('auth').find('user').attrib['nsid']

    print 'Updating: %s, %s' % (userid, token)

    update_attributes(DONATION_SERVER, 'userid', userid, 'token', token)

    bottle.response.set_cookie('token', token, path='/')
    bottle.response.set_cookie('userid', userid, path='/')
    bottle.redirect('/')

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
    #bottle.run(host='localhost', port=8080, reloader=True)
    bottle.run(server=bottle.CherryPyServer, reloader=True)

if __name__ == '__main__':
    main()
