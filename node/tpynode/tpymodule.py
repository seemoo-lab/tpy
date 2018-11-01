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
# Website:       https:://www.seemoo.de/dsteinmetzer
# Date:          2018-05-11
# Last Modified: 2018-07-17

import logging
import Pyro4


class TPyModule:
    """TPyModule

    An abstract TPyModule to be inherited by other Modules
    """

    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        self.logger.info('New Module instantiated')

    def _set_params_from_kwargs(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @Pyro4.expose
    def echo(self, message):
        return message
