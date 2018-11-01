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
# Date:          2018-04-04

import configparser


class Devices:

    def __init__(self, file=None):
        self._config = configparser.ConfigParser()
        if file:
            self.load(file)

    def __iter__(self):
        return iter(self.get())

    def load(self, file):
        self._config.read(file)

    def list(self):
        return [x for x in self._config.sections() if not x == 'DEFAULT']

    def get(self, device=None):
        if device is None:
            return [self.get(dev) for dev in self.list()]
        info = dict(self._config['DEFAULT'])
        if device not in self.list():
            return None
        device_info = dict(self._config[device])
        info.update(device_info)
        info['name'] = device
        return info

    def store(file):
        raise NotImplemented('Not yet implemented')
