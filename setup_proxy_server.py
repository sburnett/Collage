#!/usr/bin/env python

from distutils.core import setup

setup(name='Collage',
      version='1.0',
      description='A censorship-resistent message layer',
      author='Sam Burnett',
      url='http://www.gtnoise.net/collage',
      packages=['collage'
               ,'collage_donation'
               ,'collage_apps'
               ],
      requires=['pycrypto'
               ,'numpy'
               ,'flickrapi'
               ,'Imaging'
               ]
      )
