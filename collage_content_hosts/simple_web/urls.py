from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^(?P<ident>[^/]*)$', views.identifier),
    (r'^(?P<ident>[^/]*)/(?P<seq>\d+)/preview$', views.preview),
    (r'^(?P<ident>[^/]*)/(?P<seq>\d+)$', views.picture),
    # Example:
    # (r'^simple_web/', include('simple_web.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
