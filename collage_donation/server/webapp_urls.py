"""Web application that provides client access to vector donation.

We use Django because djangorpc provides convenient XML-RPC.

"""

import datetime
import xmlrpclib

from django.conf.urls.defaults import *
from django.conf import settings

from djangorpc import xmlrpc, call_xmlrpc
from database import DonaterDatabase

@xmlrpc('donate')
def donate(data, application, attributes, expiration=86400):
    """Donate a vector for use by a particular application.
    
    This returns a key which should be used to poll for the vector.
    
    """
    db = DonaterDatabase(settings.DB_DIR)
    tdexpiration = datetime.timedelta(0, expiration)
    return db.donate(data.data, application, attributes, tdexpiration)

@xmlrpc('retrieve')
def retrieve(key):
    """Poll for a donated vector.

    If an empty string is returned, then the poll has failed (i.e., no
    data is available yet). Otherwise, the vector is returned.

    """
    db = DonaterDatabase(settings.DB_DIR)
    data = db.collect(key)
    if data is None:
        return ''
    else:
        return xmlrpclib.Binary(data)

@xmlrpc('update_attributes')
def update_attributes(*args):
    """Update some attributes on a donated vector.

    See database.py

    """
    db = DonaterDatabase(settings.DB_DIR)
    db.update_attributes(*args)
    return ''

urlpatterns = patterns('',
        (r'^.*$', call_xmlrpc),
)
