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
# File:          __init__.py
# Date:          2018-02-05
# Last Modified: 2018-07-17
#

import logging

from .devices import Devices
from .tpycontrol import TPyControl
from .utils import *

# -----------------------------------------------------------------------------
# --- Logger Settings ---------------------------------------------------------
# -----------------------------------------------------------------------------

log_format = '%(asctime)s %(levelname)-5s %(message)s'
log_level = logging.INFO

formatter = logging.Formatter(log_format)
logging.basicConfig(level=log_level,
                    format=log_format)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)
