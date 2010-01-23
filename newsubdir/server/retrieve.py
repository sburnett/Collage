#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()
import sys

import database


form = cgi.FieldStorage()
if 'key' not in form:
    print 'Content-Type: text/html'
    print
    print '<html><body>'
    print 'Missing paramter <i>key</i>'
    print '</body></html>'
else:
    db = database.DonationDatabase('/tmp/donation.sqlite', 'test', '/tmp/vectors')
    key = form['key'].value
    data = db.collect(key)

    if data is None:
        print 'Content-Type: text/html'
        print
        print 'none'
    else:
        print 'Content-Type: application/octet-stream'
        print
        sys.stdout.write(data)
