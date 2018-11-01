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
# Project:       TPY - The Testbed Experimentation Framework
# Date:          2018-03-20

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='tpycontrol',

    version_format='{tag}.{commitcount}+{gitsha}',

    description='TPy Controller',
    long_description='TPy Experimentation Framework Controller',

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
    install_requires=['setuptools', 'setuptools-git-version', 'tabulate',
                      'scapy', 'fire', 'numpy', 'matplotlib', 'pandas', 'pyro4'],

    # setup_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies).
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    package_data={
        'tpycontrol': ['data/*'],
    },

    zip_safe=False,  # don't use eggs

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'tpy=tpycontrol.cli:main',
        ],
    },
)
