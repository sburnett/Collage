from django.conf.urls.defaults import *

import os.path

from django.views.static import serve

import collage_donation.client.flickr_web_client.webapp_views as views
from collage_donation.client.flickr_web_client.webapp_settings import PROJECT_PATH

urlpatterns = patterns('',
        (r'^$', views.login),
        (r'^login$', views.login),
        (r'^logout$', views.logout),
        (r'^upload$', views.upload),
        (r'^upload_file$', views.upload_file),
        (r'^callback$', views.callback),
        (r'^thumbnail$', views.thumbnail),
        (r'^thumbnail_cancel$', views.thumbnail_cancel),
)
