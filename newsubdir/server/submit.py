#!/usr/bin/env python

import cgi
import cgitb
import os
import datetime
cgitb.enable()

import database

print 'Content-Type: text/html'
print

form = cgi.FieldStorage()
if 'data' not in form or 'application' not in form:
    print '<html><body>'
    print '<h1>Vector submission</h1>'
    print '<form method="POST" enctype="multipart/form-data" action="%s">' \
            % os.environ['SCRIPT_NAME']
    print 'Data file:'
    print '<input type="file" name="data"/>'
    print '<br/>'
    print 'Expiration, seconds from submission:'
    print '<input type="text" name="expiration"/>'
    print '<br/>'
    print 'Application:'
    print '<input type="text" name="application"/>'
    print '<br/>'
    print 'Attributes (key, value)'
    print '<input type="text" name="key0"/><input type="text" name="val0"/>'
    print '<br/>'
    print '<input type="text" name="key1"/><input type="text" name="val1"/>'
    print '<br/>'
    print '<input type="text" name="key2"/><input type="text" name="val2"/>'
    print '<br/>'
    print '<input type="text" name="key3"/><input type="text" name="val3"/>'
    print '<br/>'
    print '<input type="text" name="key4"/><input type="text" name="val4"/>'
    print '<br/>'
    print '<input type="text" name="key5"/><input type="text" name="val5"/>'
    print '<br/>'
    print '<input type="text" name="key6"/><input type="text" name="val6"/>'
    print '<br/>'
    print '<input type="text" name="key7"/><input type="text" name="val7"/>'
    print '<br/>'
    print '<input type="text" name="key8"/><input type="text" name="val8"/>'
    print '<br/>'
    print '<input type="text" name="key9"/><input type="text" name="val9"/>'
    print '<br/>'
    print '<input type="submit"/>'
    print '</form>'
    print '</body></html>'
elif form['data'].file:
    data = form['data'].file.read()
    application = form['application'].value
    attributes = []
    attrib_count = 0
    while True:
        key = 'key%d' % attrib_count
        value = 'val%d' % attrib_count
        if key in form and value in form and len(form[key].value) > 0:
            attributes.append((form[key].value, form[value].value))
            attrib_count += 1
        else:
            break

    try:
        seconds = int(form['expiration'].value)
        expiration = datetime.timedelta(0, seconds)
    except:
        expiration = datetime.timedelta(1,)

    db = database.DonationDatabase('/tmp/donation.sqlite', 'test', '/tmp/vectors')
    key = db.donate(data, application, attributes, expiration)

    print key
else:
    print 'Submission error'
