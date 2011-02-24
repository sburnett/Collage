import base64

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.html import escape

import models

import pdb

def index(request):
    return render_to_response('index.tpl')

first_run = True

def update(request):
    story_id = int(request.REQUEST['story_id'])
    queued_id = int(request.REQUEST['queued_id'])
    embedding_id = int(request.REQUEST['embedding_id'])
    uploaded_id = int(request.REQUEST['uploaded_id'])

    stories = models.Stories.objects.filter(rowid__gt=story_id).order_by('-rowid')
    queued_photos = models.PhotosQueued.objects.filter(rowid__gt=queued_id).order_by('-rowid')
    embedding_photos = models.PhotosEmbedding.objects.filter(rowid__gt=embedding_id).order_by('-rowid')
    uploaded_photos = models.PhotosUploaded.objects.filter(rowid__gt=uploaded_id).order_by('-rowid')

    stories_xml = []
    for story in stories:
        stories_xml.append('<story id="%d">%s</story>' % (story.rowid, escape(story.story)))

    queued_xml = []
    for photo in queued_photos:
        queued_xml.append('<queued id="%d" identifier="%s"/>' % (photo.rowid, photo.identifier))

    embedding_xml = []
    for photo in embedding_photos:
        embedding_xml.append('<embedding id="%d" identifier="%s"/>' % (photo.rowid, photo.identifier))

    uploaded_xml = []
    for photo in uploaded_photos:
        uploaded_xml.append('<uploaded id="%d" identifier="%s"/>' % (photo.rowid, photo.identifier))

    global first_run
    if first_run:
        refresh_xml = '<refresh/>'
        first_run = False
    else:
        refresh_xml = ''

    update_xml = '<update>%s%s%s%s%s</update>' % (''.join(stories_xml),
                                                ''.join(queued_xml),
                                                ''.join(embedding_xml),
                                                ''.join(uploaded_xml),
                                                refresh_xml)
    print update_xml
    return HttpResponse(update_xml, 'text/xml')

def article(request):
    id = int(request.REQUEST['id'])
    article = models.Stories.objects.get(rowid=id)
    return HttpResponse(article.story)

def get_thumbnail(request, cl):
    id = int(request.REQUEST['id'])
    photo = cl.objects.get(rowid=id)
    return HttpResponse(base64.b64decode(photo.thumbnail), 'image/jpeg')

def queued(request):
    return get_thumbnail(request, models.PhotosQueued)
def embedding(request):
    return get_thumbnail(request, models.PhotosEmbedding)
def uploaded(request):
    return get_thumbnail(request, models.PhotosUploaded)
