import os.path

from django.conf.urls.defaults import *

import collage_vis.photovis.views as views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^update$', views.update),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')}),
    (r'^article', views.article),
    (r'^queued', views.queued),
    (r'^embedding', views.embedding),
    (r'^uploaded', views.uploaded),
)
