from django.conf.urls.defaults import *

from django.views.static import serve

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
        (r'^/static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
        (r'^$', 'views.index'),
        (r'^/login$', 'views.login'),
        (r'^/logout$', 'views.logout'),
        (r'^/upload$', 'views.upload'),
        (r'^/upload_file$', 'views.upload_file'),
        (r'^/callback$', 'views.callback'),
)
