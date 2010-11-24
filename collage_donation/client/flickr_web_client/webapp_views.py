"""A Django Web application for donating Flickr photos to Collage.

Users are authenticated using the Flickr API.

"""

import flickrapi
import urllib
import re
import sys
import os
import StringIO
import sqlite3
import tempfile
from optparse import OptionParser

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.conf import settings

import Image

from collage_donation.client.rpc import submit, update_attributes

import pdb

script_path = os.path.dirname(sys.argv[0])
def template_path(name):
    return os.path.join(script_path, 'views', '%s.tpl' % name)

flickr = flickrapi.FlickrAPI(settings.FLICKR_API_KEY, settings.FLICKR_SECRET, store_token=False)

DONATION_SERVER = 'https://127.0.0.1:8000/server.py'
APPLICATION_NAME = 'proxy_community'
UPLOADS_DIR = os.path.abspath('uploads')

def check_credentials(request):
    if 'token' not in request.session or \
            'userid' not in request.session:
        return False

    token = request.session['token']
    f = flickrapi.FlickrAPI(settings.FLICKR_API_KEY, settings.FLICKR_SECRET, token=token, store_token=False)
    try:
        f.auth_checkToken()
    except flickrapi.FlickrError:
        return False

    return True

def wait_for_key(key, title, token, tags):
    conn = sqlite3.connect(settings.WAITING_DB)
    cur = conn.execute('''INSERT INTO waiting (key, title, token)
                                       VALUES (?, ?, ?)''',
                       (key, title, token))
    rowid = cur.lastrowid
    for tag in tags:
        conn.execute('INSERT INTO tags (tag, waiting_id) VALUES (?, ?)', (tag, rowid))
    conn.commit()
    conn.close()

def index(request):
    if check_credentials(request):
        return HttpResponseRedirect('/upload')
    else:
        return HttpResponseRedirect('/login')

def login(request):
    return render_to_response('login.tpl', {'login_url': flickr.web_login_url(perms='write')})

def logout(request):
    if 'token' in request.session:
        del request.session['token']
    if 'userid' in request.session:
        del request.session['userid']
    return HttpResponseRedirect('/')

def is_valid_filename(filename):
    return filename is not None \
            and len(filename) > 0 \
            and os.path.exists(filename) \
            and os.path.samefile(UPLOADS_DIR, os.path.dirname(os.path.abspath(filename)))

def upload(request):
    if not check_credentials(request):
        return HttpResponseRedirect('/login')

    print 'Vector ids: %s' % request.REQUEST.get('vector_ids')

    vector_ids = request.REQUEST.get('vector_ids')
    if vector_ids:
        vectors = vector_ids.split(';')
    else:
        vectors = None

    args = {'token': request.session['token'],
            'userid': request.session['userid'],
            'username': request.session['username'],
            'vector_ids': vector_ids,
            'title': request.REQUEST.get('title'),
            'expiration': request.REQUEST.get('expiration'),
            'vectors': vectors}

    submit_button = request.REQUEST.get('submit')

    if submit_button is None:
        return render_to_response('upload.tpl', args)

    title = request.REQUEST.get('title')
    vector_ids = request.REQUEST.get('vector_ids')
    numtags = request.REQUEST.get('numtags')
    expiration = request.REQUEST.get('expiration')

    try:
        for idx in range(max(int(numtags), 200)):
            name = 'check%d' % idx
            if name in request.REQUEST:
                args[name] = ", checked: true"
    except ValueError:
        pass

    if title is None or len(title) == 0:
        args['error'] = 'You must enter a title'
        return render_to_response('upload.tpl', args)

    if expiration is None:
        args['expiration'] = 'You must specify an expiration time'
        return render_to_response('upload.tpl', args)

    if vector_ids is None or numtags is None:
        args['error'] = 'Form error'
        return render_to_response('upload.tpl', args)

    title = title.strip()
    filenames = vector_ids.split(';')
    for filename in filenames:
        if not is_valid_filename(filename):
            args['error'] = 'You must select photos to upload'
            return render_to_response('upload.tpl', args)

    try:
        numtags = int(numtags.strip())
    except ValueError:
        args['error'] = 'Inconsistent upload state. Please try again.'
        return render_to_response('upload.tpl', args)

    numtags = max(numtags, 200)     # Hard clamp on the number of tags, to prevent DoS
    tags = []
    for idx in range(numtags):
        name = 'check%d' % idx
        if name in request.REQUEST:
            tags.append(request.REQUEST[name])
    if len(tags) < 3:
        args['error'] = 'Please select at least 3 tags from the list'
        return render_to_response('upload.tpl', args)

    attributes = map(lambda tag: ('tag', tag), tags)

    try:
        expiration = int(expiration.strip())
    except ValueError:
        args['error'] = 'Please enter a valid number of hours'
        return render_to_response('upload.tpl', args)

    if expiration > 24 or expiration < 0:
        args['error'] = 'Expiration can be at most 24 hours'
        return render_to_response('upload.tpl', args)

    expiration = 60*60*expiration

    for filename in filenames:
        try:
            vector = open(filename, 'rb').read()
            os.unlink(filename)
            key = submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)
        except Exception as e:
            args['error'] = 'Cannot contact upload server. Please try again later.'
            return render_to_response('upload.tpl', args)

        wait_for_key(key, title, request.session['token'], tags)

    args['expiration'] = expiration/(60*60)
    return render_to_response('process.tpl', args)

def upload_file(request):
    if not check_credentials(request):
        return HttpResponseBadRequest()

    vector = request.raw_post_data

    if len(vector) > 10*1024*1024:
        return HttpResponse('{"success": false, "error": "Maximum photo size is 10 MB"}')

    token = request.session['token']
    userid = request.session['userid']

    f = flickrapi.FlickrAPI(settings.FLICKR_API_KEY, settings.FLICKR_SECRET, token=token, store_token=False)
    try:
        f.auth_checkToken()
    except flickrapi.FlickrError:
        return HttpResponseBadRequest()

    outf = tempfile.NamedTemporaryFile(suffix='.jpg', prefix='upload', dir=UPLOADS_DIR, delete=False)
    outf.write(vector)
    outf.close()

    return HttpResponse('{"success": true, "filename": "%s"}' % outf.name)

def thumbnail(request):
    if not check_credentials(request):
        return HttpResponseBadRequest()

    filename = request.REQUEST.get('filename')
    if not is_valid_filename(filename):
        return HttpResponseBadRequest()

    img = Image.open(filename)
    img.thumbnail((128, 128))
    outfile = StringIO.StringIO()
    img.save(outfile, 'JPEG')
    return HttpResponse(outfile.getvalue(), 'image/png')

def thumbnail_cancel(request):
    if not check_credentials(request):
        return HttpResponseBadRequest()

    filename = request.REQUEST.get('filename')
    if not is_valid_filename(filename):
        return HttpResponseBadRequest()

    os.unlink(filename)

def callback(request):
    frob = request.REQUEST.get('frob')
    if not frob:
        return HttpResponseBadRequest()

    token = flickr.get_token(frob)

    f = flickrapi.FlickrAPI(settings.FLICKR_API_KEY, settings.FLICKR_SECRET, token=token, store_token=False)
    try:
        response = f.auth_checkToken()
    except flickrapi.FlickrError:
        return HttpResponseRedirect('/login')

    userid = response.find('auth').find('user').attrib['nsid']
    response = flickr.people_getInfo(user_id=userid)
    username = response.find('person').find('username').text
    ispro = response.find('person').attrib['ispro']
    if ispro != '1':
        return HttpResponseRedirect('/static/notpro.html')

    print 'Updating: %s, %s' % (userid, token)

    update_attributes(DONATION_SERVER, 'userid', userid, 'token', token)

    request.session['token'] = token
    request.session['userid'] = userid
    request.session['username'] = username
    return HttpResponseRedirect('/upload')
