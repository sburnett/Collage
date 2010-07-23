import datetime
import xmlrpclib

from django.conf.urls.defaults import *
from django.conf import settings

from djangorpc import xmlrpc, call_xmlrpc
from database import DonaterDatabase

@xmlrpc('donate')
def donate(data, application, attributes, expiration=86400):
    db = DonaterDatabase(settings.DB_DIR)
    tdexpiration = datetime.timedelta(0, expiration)
    return db.donate(data.data, application, attributes, tdexpiration)

@xmlrpc('retrieve')
def retrieve(key):
    db = DonaterDatabase(settings.DB_DIR)
    data = db.collect(key)
    if data is None:
        return ''
    else:
        return xmlrpclib.Binary(data)

@xmlrpc('update_attributes')
def update_attributes(*args):
    db = DonaterDatabase(settings.DB_DIR)
    db.update_attributes(*args)
    return ''

urlpatterns = patterns('',
        (r'^.*$', call_xmlrpc),
)
