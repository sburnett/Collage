#!/usr/bin/env python

from bottle import route, view
import bottle
import flickrapi
import urllib
import re
import sys
import StringIO

import Image

import rpc

import pdb

bottle.debug(True)

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

flickr = flickrapi.FlickrAPI(api_key, api_secret, store_token=False)

DONATION_SERVER = 'http://127.0.0.1:8000'
APPLICATION_NAME = 'proxy'

def get_latest_tags():
    pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
    match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
    block = match.group(1)
    of = open('views/tags.tpl', 'w')
    matches = re.finditer(r'<a href=".*?" style="font-size: (?P<size>\d+)px;">(?P<tag>.*?)</a>', block)
    for (idx, match) in enumerate(matches):
        print >>of, '(new YAHOO.widget.Button({ type: "checkbox", label: "%s", id: "check%d", name: "check%d", value: "%s", container: "tagsbox"})).setStyle("font-size", "%spx");' % (match.group('tag'), idx, idx, match.group('tag'), match.group('size'))
    print >>of, 'document.write("<input type=\'hidden\' name=\'numtags\' value=\'%d\'/>");' % (idx+1)
    of.close()

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
    return bottle.send_file(filename, 'static')

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
    return dict()

@route('/upload', method='POST')
def process():
    if not check_credentials():
        bottle.redirect('/login')
    elif 'submit' not in bottle.request.POST:
        bottle.redirect('/upload')
    else:
        response = flickr.people_getInfo(user_id=userid)
        ispro = response.find('person').attrib['ispro'] == '1'

        title = bottle.request.POST.get('title', '').strip()
        uploaded = bottle.request.POST.get('vector')
        if uploaded == '':
            return bottle.template('upload', error='You must select a photo to upload')

        data = uploaded.file.read()
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

        try:
            numtags = int(bottle.request.POST.get('numtags', '').strip())
        except ValueError:
            return bottle.template('upload', error='Inconsistent upload state. Please try again.')
        numtags = max(numtags, 200)     # Hard clamp on the number of tags, to prevent DoS
        tags = []
        for idx in range(numtags):
            name = 'check%d' % idx
            if name in bottle.request.POST:
                tags.append(bottle.request.POST[name])
        if len(tags) < 3:
            return bottle.template('upload', error='Please select at least 3 tags from the list')
        try:
            expiration = 60*60*int(bottle.request.POST.get('expiration', '').strip())
        except ValueError:
            return bottle.template('upload', error='Please enter a valid number of hours')
        token = bottle.request.COOKIES['token']
        userid = bottle.request.COOKIES['userid']

        attributes = map(lambda tag: ('tag', tag), tags)
        attributes.append(('title', title))
        attributes.append(('client', 'web'))
        attributes.append(('token', token))
        attributes.append(('userid', userid))
        attributes.append(('ispro', ispro))

        try:
            rpc.submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)
        except:
            return bottle.template('upload', error='Cannot contact upload server. Please try again later.')

        return bottle.template('process', expiration=expiration/(60*60))

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

    rpc.update_attributes(DONATION_SERVER, 'userid', userid, 'token', token)

    bottle.response.set_cookie('token', token, path='/')
    bottle.response.set_cookie('userid', userid, path='/')
    bottle.redirect('/')

get_latest_tags()
bottle.run(host='localhost', port=8080, reloader=True)
