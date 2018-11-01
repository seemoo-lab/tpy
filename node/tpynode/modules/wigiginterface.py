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
# Date:          2018-05-14
# Last Modified: 2018-10-31

import logging
import Pyro4
from .wigigwmi import WiGigWMI
from .rfantenna import RFAntenna

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WiGigInterface (WiGigWMI, RFAntenna):

    """WiGigInterface Module.
    Provides control over an Wireless IEEE 802.11ad Interface.
    """

    def __init__(self, **kwargs):
        super(WiGigInterface, self).__init__(**kwargs)

    @Pyro4.expose
    def select_enabled_tx_sectors(self, sectors, cid):
        order = sectors + ([0xff] * (128 - len(sectors)))
        n = len(sectors)
        if self.wmi_prio_tx_sectors_order(order, 0x02, cid):
            raise Exception('Error setting sector order')
        if self.wmi_prio_tx_sectors_number(n, n, cid):
            raise Exception('Error setting sector number')
