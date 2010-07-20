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
                 ,'collage_donation.server'
                 ,'collage_donation.client'
                 ,'collage_donation.client.flickr_web_client'
                 ,'collage_apps'
                 ,'collage_apps.tasks'
                 ,'collage_apps.vectors'
                 ,'collage_apps.providers'
                 ,'collage_apps.proxy'
                 ],
        install_requires=['pycrypto'
                         ,'numpy'
                         ,'flickrapi'
                         ],
        scripts=['run-proxy-server.sh'],
        )
