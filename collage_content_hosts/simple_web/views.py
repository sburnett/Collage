"""A simple content host of testing Collage.

This content host serves a directory of donated Collage photos, with minimal
extra interface. It definitely isn't meant for production use.

"""

import os.path
import glob

from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.shortcuts import render_to_response

def index(request):
    idents = []
    for ident in glob.iglob(os.path.join(settings.CONTENT_HOST_ROOT, '*')):
        idents.append(os.path.basename(ident))

    return render_to_response('index.tpl', {'idents': idents})

def identifier(request, ident):
    photo_path = os.path.abspath(os.path.join(settings.CONTENT_HOST_ROOT, ident))
    if not os.path.samefile(settings.CONTENT_HOST_ROOT, os.path.dirname(photo_path)) \
            or not os.path.isdir(photo_path):
        return HttpResponseNotFound()

    photos = []
    for photo in glob.iglob(os.path.join(photo_path, '*.jpg')):
        photos.append(os.path.splitext(os.path.basename(photo))[0])

    return render_to_response('identifier.tpl', {'ident': ident, 'photos': photos})

def preview(request, ident, seq):
    return render_to_response('preview.tpl', {'ident': ident, 'photo': seq})

def picture(request, ident, seq):
    photo_name = '%s.jpg' % seq
    photo_path = os.path.abspath(os.path.join(settings.CONTENT_HOST_ROOT, ident, photo_name))
    if not os.path.samefile(settings.CONTENT_HOST_ROOT, os.path.dirname(os.path.dirname(photo_path))) \
            or not os.path.isfile(photo_path):
        return HttpResponseNotFound()

    photo = open(photo_path, 'rb').read()
    return HttpResponse(photo, 'image/jpeg')
