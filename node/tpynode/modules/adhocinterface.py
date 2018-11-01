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
import socket
import fcntl
import struct
import pyric.pyw as pyw     # iw functionality

from .wifiinterface import WiFiInterface

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AdHocInterface(WiFiInterface):

    def __init__(self, **kwargs):
        super(AdHocInterface, self).__init__(**kwargs)
        self._card = pyw.getcard(self.iface)
        self._channel = int(kwargs.get('channel', 1))
        self._bssid = kwargs.get('bssid', 'c0:ff:ee:c0:ff:ee')
        self._ssid = kwargs.get('ssid', 'erlab')
        self._mode = kwargs.get('mode', 'HT20')
        self._ipaddress = kwargs.get('ipaddress', '10.0.0.1')
        ipaddress_auto_dev = kwargs.get('ipaddress_auto_dev', None)
        if self._ipaddress == 'auto' and ipaddress_auto_dev is not None:
            self._ipaddress = self._ipaddress_auto(ipaddress_auto_dev)
        logger.info('Adhoc dev {}, addr {}'.format(self.iface, self._ipaddress))
        logger.info('SSID {}, BSSID {}, channel {}, mode {}'.format(self._ssid, self._bssid, self._channel, self._mode))

    @Pyro4.expose
    def up(self):
        self._ip_link_up()
        self._iw_set_type()
        self._iw_ibss_join()
        self._ip_address_add()

    @Pyro4.expose
    def down(self):
        self._ip_address_flush()
        self.ip_route_flush()
        self._iw_ibss_leave()
        self._ip_link_down()

    @Pyro4.expose
    @property
    def ipaddress(self):
        return pyw.ifaddrget(self._card)[0]

    @Pyro4.expose
    @property
    def macaddress(self):
        return pyw.macget(self._card)

    def _iw_set_type(self, type='ibss'):
        cmd = ['iw', 'dev', self.iface, 'set', 'type', type]
        return subprocess.run(cmd)

    def _iw_ibss_join(self):
        frequency = self._channel_to_frequency(self._channel)
        cmd = ['iw', 'dev', self.iface, 'ibss', 'join', self._ssid, str(frequency), self._mode, self._bssid]
        return subprocess.run(cmd)

    def _iw_ibss_leave(self):
        cmd = ['iw', 'dev', self.iface, 'ibss', 'leave']
        return subprocess.run(cmd)

    @Pyro4.expose
    def iw_station_dump(self):
        cmd = ['iw', 'dev', self.iface, 'station', 'dump']
        return subprocess.check_output(cmd).decode()

    def _ip_link_up(self):
        cmd = ['ip', 'link', 'set', 'dev', self.iface, 'up']
        return subprocess.run(cmd)

    def _ip_link_down(self):
        cmd = ['ip', 'link', 'set', 'dev', self.iface, 'down']
        return subprocess.run(cmd)

    def _ip_address_flush(self):
        cmd = ['ip', 'address', 'flush', 'dev', self.iface]
        return subprocess.run(cmd)

    def _ip_address_add(self):
        cmd = ['ip', 'address', 'add', '{}/16'.format(self._ipaddress), 'brd', '+', 'dev', self.iface]
        return subprocess.run(cmd)

    @Pyro4.expose
    def ip_route_flush(self):
        cmd = ['ip', 'route', 'flush', 'dev', self.iface]
        subprocess.run(cmd)

    @staticmethod
    def _channel_to_frequency(channel):
        channel_map = {
            # 2.4 GHz band
            1: 2412,
            6: 2437,
            11: 2462,
            13: 2472,
            14: 2484,
            # 5 GHz band (20 MHz channels)
            36: 5180,
        }
        return channel_map.get(channel)

    @staticmethod
    def _ipaddress_auto(ipaddress_auto_dev):
        ipaddr = AdHocInterface._get_ipaddress(ipaddress_auto_dev)
        prefix = '10.0.0.'
        suffix = ipaddr.split('.')[3]
        ipaddress_auto = prefix + suffix
        logger.info('Setting interface address to {}'.format(ipaddress_auto))
        return ipaddress_auto

    @staticmethod
    def _get_ipaddress(ifname):
        # from https://stackoverflow.com/a/24196955
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', bytes(ifname[:15], 'utf-8'))
        )[20:24])
