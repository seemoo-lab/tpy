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
# Author:        Milan Stute
# E-Mail:        mstute@seemoo.tu-darmstadt.de
# Website:       https:://www.seemoo.de/dsteinmetzer
# Date:          2018-05-08
# Last Modified: 2018-10-31

import logging
import subprocess
import Pyro4

from tpynode import TPyModule

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Ping(TPyModule):

    def __init__(self, **kwargs):
        super(Ping, self).__init__(**kwargs)
        self._bin = kwargs.get('bin', 'ping')

    @Pyro4.expose
    def ping(self, address='localhost', count=4, interval=None, interface=None):
        cmd = [self._bin]
        if count is not None:
            cmd.extend(['-c', str(count)])
        if interval is not None:
            cmd.extend(['-i', str(interval)])
        if interface is not None:
            cmd.extend(['-I', interface])
        cmd.append(address)
        return subprocess.call(cmd) is 0
