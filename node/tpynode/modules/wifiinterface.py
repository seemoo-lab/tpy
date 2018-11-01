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
# Last Modified: 2018-07-17

import logging
import Pyro4
import pyric                # pyric errors
import pyric.pyw as pyw     # iw functionality
import subprocess
import time

from .interface import Interface
from tpynode import TPyModule
from ..tools import link


logger = logging.getLogger(__name__)


class WiFiInterface(Interface):

    """Interface.

    A module to control a wireless interface.
    """

    def __init__(self, **kwargs):
        self._interface = kwargs.get('interface', None)
        super(WiFiInterface, self).__init__(**kwargs)

    @Pyro4.expose
    @property
    def iface(self):
        return self._interface

    @Pyro4.expose
    def get_ipaddr(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.ifaddrget(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_hwaddr(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.macget(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def set_hwaddr(self, addr):
        try:
            w = pyw.getcard(self._interface)
            pyw.macset(w, addr)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def set_ipaddr(self, addr=None, mask=None, bcast=None):
        try:
            w = pyw.getcard(self._interface)
            pyw.ifaddrset(w, addr, mask, bcast)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_link(self):
        return link.get_iw_link(self._interface)

    @Pyro4.expose
    def get_stations(self):
        return link.get_iw_station_dump(self._interface)

    @Pyro4.expose
    def set_down(self):
        try:
            w = pyw.getcard(self._interface)
            pyw.down(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def set_up(self):
        try:
            w = pyw.getcard(self._interface)
            pyw.up(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def is_up(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.isup(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def is_connected(self):
        return self.is_up and self.get_stations()

    @Pyro4.expose
    def is_connected_to(self, peer):
        if self.is_up:
            for sta in self.get_stations():
                if sta and sta['mac'] == peer:
                    return True
        return False

    @Pyro4.expose
    def wait_for_peer(self, peer, timeout=10):
        tic = time.time()
        logger.info('Waiting for Connection ...')
        while(time.time() < (tic + timeout)):
            try:
                if self.is_connected_to(peer):
                    logger.debug('Connection established after %.2f seconds' %
                                 (time.time() - tic))
                    return True
            except IndexError:
                logger.error('Index error while checking connectivity ...')
        raise TimeoutError('Connection to %s timed out after %.2f seconds' %
                           (peer, timeout))

    @Pyro4.expose
    def set_mtu(self, mtu):
        cmd = ['ifconfig', self._interface, 'mtu', str(mtu)]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode:
            raise Exception('Error setting MTU on interface')

    @Pyro4.expose
    def get_iface_info(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.ifinfo(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_dev_info(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.devinfo(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_phy_info(self):
        try:
            w = pyw.getcard(self._interface)
            return pyw.phyinfo(w)
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_phy_id(self):
        try:
            w = pyw.getcard(self._interface)
            return w.phy
        except pyric.error as e:
            logger.error(e)

    @Pyro4.expose
    def get_dev_mode(self):
        return self.get_dev_info()['mode']

    @Pyro4.expose
    def get_signal_strength_for_peer(self, peer, timeout=3):
        tic = time.time()
        while time.time() < (tic + timeout):
            station_dump = [x for x in self.get_stations()
                            if x['mac'] == peer]
            if station_dump:
                return station_dump[0]['signal']
        raise TimeoutError('Timeout reading signal strength for device')
