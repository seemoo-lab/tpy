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
# Date:          2018-04-05

import sys
import logging
import Pyro4

sys.excepthook = Pyro4.util.excepthook

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TPyRemoteModule:

    def __init__(self, name, host, port, **kwargs):

        # Establish connection
        uri = self._pyro_proxy_uri(name, host, port)
        self._proxy = Pyro4.core.Proxy(uri)

        # Bind, so meta data will be available
        try:
            self._proxy._pyroBind()
        except Pyro4.errors.CommunicationError:
            raise ConnectionError()

        # Wrap all Pyro Proxy Methods
        for m in self.remote_methods:
            setattr(self, m, getattr(self._proxy, m))
        for a in self.remote_attributes:
            # TODO cache attributes
            setattr(self, a, getattr(self._proxy, a))

        self._name = name
        self._host = host
        self._port = port

    @property
    def name(self):
        return self._name

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def proxy_uri(self):
        return self._pyro_proxy_uri(self.name, self.host, self.port)

    @property
    def remote_methods(self):
        return self._proxy._pyroMethods

    @property
    def remote_attributes(self):
        return self._proxy._pyroAttrs

    @staticmethod
    def _pyro_proxy_uri(name, host, port):
        return 'PYRO:{}@{}:{}'.format(name, host, port)
