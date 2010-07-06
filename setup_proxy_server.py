#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
        name='CollageProxyServer',
        version='1.0',
        description='A censorship-resistent message layer',
        author='Sam Burnett',
        url='http://www.gtnoise.net/collage',
        packages=['collage'
                 ,'collage_donation'
                 ,'collage_apps'
                 ],
        install_requires=['pycrypto'
                         ,'numpy'
                         ,'flickrapi'
#                         ,'Imaging'
                         ]
        )
