#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
        name='CollageProxyClient',
        version='1.0',
        description='A censorship-resistent message layer',
        author='Sam Burnett',
        url='http://www.gtnoise.net/collage',
        packages=['collage'
                 ,'collage_apps.proxy.taskmodules'
                 ],
        py_modules=['collage_apps.providers.flickr'
                   ,'collage_apps.providers.local'
                   ,'collage_apps.vectors.jpeg'
                   ,'collage_apps.proxy.proxy_client'
                   ,'collage_apps.proxy.proxy_common'
                   ,'collage_apps.instruments'
                   ,'ez_setup'
                   ],
        install_requires=['pycrypto'
                         ],
        scripts=['collage_demo']
        )
