from bottle import route, view
import bottle
import flickrapi

import rpc

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

flickr = flickrapi.FlickrAPI(api_key, api_secret, store_token=False)

DONATION_SERVER = 'http://127.0.0.1:8000'
APPLICATION_NAME = 'test'

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

@route('/upload')
@view('upload')
def upload():
    return dict()

@route('/process', method='POST')
@view('process')
def process():
    if 'token' not in bottle.request.COOKIES:
        bottle.redirect('/login')
    elif 'submit' not in bottle.request.POST:
        bottle.redirect('/upload')
    else:
        title = bottle.request.POST.get('title', '').strip()
        vector = bottle.request.POST.get('vector').file.read()
        tags = bottle.request.POST.get('tags', '').strip().split()
        expiration = int(bottle.request.POST.get('expiration', '').strip())
        token = bottle.request.COOKIES['token']

        attributes = map(lambda tag: ('tag', tag), tags)
        attributes.append(('title', title))
        attributes.append(('token', token))

        rpc.submit(DONATION_SERVER, vector, APPLICATION_NAME, attributes, expiration)

        return {'expiration': expiration}

@route('/callback')
def callback():
    frob = bottle.request.GET['frob']
    token = flickr.get_token(frob)
    bottle.response.set_cookie('token', token, path='/')
    bottle.redirect('/')

bottle.run(host='localhost', port=8080)
