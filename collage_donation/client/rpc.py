"""Client end of Collage donation RPC."""

import xmlrpclib

def submit(url, data, application, attributes, expiration):
    proxy = xmlrpclib.ServerProxy(url)
    packed = xmlrpclib.Binary(data)
    return proxy.donate(packed, application, attributes, expiration)

def retrieve(url, key):
    proxy = xmlrpclib.ServerProxy(url)
    return proxy.retrieve(key)

def update_attributes(url, key, value, new_key, new_value):
    proxy = xmlrpclib.ServerProxy(url)
    proxy.update_attributes(key, value, new_key, new_value)
