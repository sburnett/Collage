#!/usr/bin/env python

from distutils.core import setup

setup(name='Collage Photo Donation Tool',
      version='0.1',
      description='A Flickr upload tool that helps fight censorship',
      author='Sam Burnett',
      url='http://www.gtnoise.net/collage',
      scripts=['flickr_client.py', 'retrieve.py', 'submit.py'],
      requires='flickrapi',
      )
