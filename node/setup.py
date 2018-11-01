#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#          ###########   ###########   ##########    ##########
#         ############  ############  ############  ############
#         ##            ##            ##   ##   ##  ##        ##
#         ##            ##            ##   ##   ##  ##        ##
#         ###########   ####  ######  ##   ##   ##  ##    ######
#          ###########  ####  #       ##   ##   ##  ##    #    #
#                   ##  ##    ######  ##   ##   ##  ##    #    #
#                   ##  ##    #       ##   ##   ##  ##    #    #
#         ############  ##### ######  ##   ##   ##  ##### ######
#         ###########    ###########  ##   ##   ##   ##########
#
#            S E C U R E   M O B I L E   N E T W O R K I N G
#
# Author:        Daniel Steinmetzer
# E-Mail:        dsteinmetzer@seemoo.tu-darmstadt.de
# Website:       https://www.seemoo.de/dsteinmetzer
# Project:       openginect
# File:          setup.py
# Date:          2018-03-20
# Last Modified: 2018-11-01
#

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='tpynode',

    version_format='{tag}.{commitcount}+{gitsha}',

    description='TPyNode',
    long_description='TPy Experimentation Framework Node',

    # The project's main homepage.
    url='https://seemoo.de/talon-tools/',

    # Author details
    author='Daniel Steinmetzer',
    author_email='dsteinmetzer@seemoo.tu-darmstadt.de',

    # Choose your license
    license='MIT',

    # What does your project relate to?
    keywords='talon',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed.
    install_requires=['setuptools-git-version', 'setuptools', 'tabulate',
                      'pyro4', 'daemonize', 'pyric', 'fire',
                      'ntplib', 'pluginbase'],

    # List additional groups of dependencies here (e.g. development
    # dependencies).
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'tpynode': ['data/*'],
    },

    zip_safe=False,  # don't use eggs

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'tpynode=tpynode.daemon:main'
        ],
    },
)
