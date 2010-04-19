#!/usr/bin/env python

from optparse import OptionParser
import time

import flickrapi

from database import UploaderDatabase

api_key = 'ebc4519ce69a3485469c4509e8038f9f'
api_secret = '083b2c8757e2971f'

PAUSE_TIME = 1

def main():
    usage = 'usage: %s [options] <database_dir>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(attributes=[])
    parser.add_option('-a', '--attribute', dest='attributes', action='append', type='string', help='Vector attributes')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Need to specify database directory')

    db = UploaderDatabase(args[0])

    attrs = []
    for attr in options.attributes:
        attrs.append(tuple(attr.split(':', 1)))

    while True:
        keys = db.collect(attrs)

        if len(keys) == 0:
            time.sleep(PAUSE_TIME)

        for key in keys:
            attributes = db.get_attributes(key)
            attr_dict = dict(attributes)

            if 'token' in attr_dict:
                token = attr_dict['token']
            else:
                db.delete(key)
                continue

            flickr = flickrapi.FlickrAPI(api_key, api_secret, token=token, store_token=False)
            
            try:
                flickr.auth_checkToken()
            except flickrapi.FlickrError:
                db.delete(key)
                continue

            tags = []
            for (k, v) in attributes:
                if k == 'tag':
                    tags.append(v)

            flickr.upload(filename=db.get_filename(key), title=attr_dict.get('title', ''), tags=' '.join(tags))
            db.delete(key)

            time.sleep(PAUSE_TIME)

if __name__ == '__main__':
    main()
