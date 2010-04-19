#!/usr/bin/env python

from bottle import route, view
import bottle
import flickrapi
import urllib
import re
import sys

import rpc

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
    output = re.sub('href=".*?"', 'href=""', block)
    open('views/tags.tpl', 'w').write(output)

@route('/')
def index():
    if 'token' in bottle.request.COOKIES:
        bottle.redirect('/upload')
    else:
        bottle.redirect('/login')

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
    return dict()

@route('/upload', method='POST')
def process():
    if 'token' not in bottle.request.COOKIES:
        bottle.redirect('/login')
    elif 'submit' not in bottle.request.POST:
        bottle.redirect('/upload')
    else:
        title = bottle.request.POST.get('title', '').strip()
        uploaded = bottle.request.POST.get('vector') 
        if uploaded == '':
            return bottle.template('upload', error='Must upload photo')
        vector = uploaded.file.read()
        tags = bottle.request.POST.get('tags', '').strip().split()
        expiration = int(bottle.request.POST.get('expiration', '').strip())
        token = bottle.request.COOKIES['token']
        userid = bottle.request.COOKIES['userid']

        attributes = map(lambda tag: ('tag', tag), tags)
        attributes.append(('title', title))
        attributes.append(('token', token))
        attributes.append(('userid', userid))

        rpc.submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)

        return bottle.template('process', expiration=expiration)

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
