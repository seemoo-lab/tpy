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
import Pyro4

from .tpyremotemodule import TPyRemoteModule

sys.excepthook = Pyro4.util.excepthook


class TPyRemoteNode(TPyRemoteModule):

    def __init__(self, host, port, **kwargs):
        super(TPyRemoteNode, self).__init__('tpynode', host, port, **kwargs)
        self._modules = {}
        self._lookup_modules()

    def __getitem__(self, module):
        return self._get_remote_module(module)

    def _get_remote_module(self, name):
        if name not in self._modules:
            try:
                self._modules[name] = TPyRemoteModule(name, self.host, self.port)
            except ConnectionError:
                raise KeyError
        return self._modules[name]

    def _lookup_modules(self):
        for module in self.modules:
            setattr(self, module, self._get_remote_module(module))
