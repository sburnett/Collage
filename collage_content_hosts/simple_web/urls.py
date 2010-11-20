from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^(?P<ident>[^/]*)$', views.identifier),
    (r'^(?P<ident>[^/]*)/(?P<seq>\d+)/preview$', views.preview),
    (r'^(?P<ident>[^/]*)/(?P<seq>\d+)$', views.picture),
)
