#!/usr/bin/python

import urllib
import re
import os.path
import time

def get_latest_tags():
    pagedata = urllib.urlopen('http://flickr.com/photos/tags').read()
    match = re.search('<p id="TagCloud">(.*?)</p>', pagedata, re.S|re.I)
    block = match.group(1)
    print os.path.abspath(os.path.curdir)
    of = open('tags.tpl', 'w')
    matches = re.finditer(r'<a href=".*?" style="font-size: (?P<size>\d+)px;">(?P<tag>.*?)</a>', block)
    for (idx, match) in enumerate(matches):
        print >>of, '(new YAHOO.widget.Button({ type: "checkbox", label: "%s", id: "check%d", name: "check%d", value: "%s", container: "tagsbox" {{check%d|default:""}} })).setStyle("font-size", "%spx");' % (match.group('tag'), idx, idx, match.group('tag'), idx, match.group('size'))
    print >>of, 'document.write("<input type=\'hidden\' name=\'numtags\' value=\'%d\'/>");' % (idx+1)
    of.close()

def main():
    while True:
        get_latest_tags()
        time.sleep(86400)

if __name__ == '__main__':
    main()
