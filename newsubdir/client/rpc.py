import xmlrpclib

def submit(url, data, application, attributes, expiration):
    proxy = xmlrpclib.ServerProxy(url)
    packed = xmlrpclib.Binary(data)
    return proxy.donate(packed, application, attributes, expiration)

def retrieve(url, key):
    proxy = xmlrpclib.ServerProxy(url)
    return proxy.retrieve(key)
