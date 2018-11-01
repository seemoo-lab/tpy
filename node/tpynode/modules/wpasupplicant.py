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
# Date:          2018-06-12
# Last Modified: 2018-08-30

import logging
import subprocess
import os
import Pyro4

from tpynode import TPyModule

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WPASupplicant(TPyModule):

    def __init__(self, **kwargs):
        super(WPASupplicant, self).__init__(**kwargs)
        self._iface = kwargs.get('interface', None)
        self._pid = os.path.join('/var/run', 'hostapd_%s.pid' % self._iface)

    @Pyro4.expose
    def set_ssid(self, ssid):
        cfgfile = '/etc/wpa_supplicant.conf'
        cmd = ['ash', '/root/files/set_wpasup_ssid.sh', ssid, cfgfile]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return p.returncode

    @Pyro4.expose
    def start(self, cfg=None):
        cfgfile = '/etc/wpa_supplicant.conf'
        cmd = ['wpa_supplicant', '-D', 'nl80211', '-i', self._iface,
               '-c', cfgfile, '-P', self._pid, '-B']
        logger.info('Starting wpa_supplicant')

        num_errors = 0
        while num_errors < 3:
            p = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

            # Log debug output
            for ll in p.stdout.decode().splitlines():
                logger.debug(ll)

            # Check response
            if p.returncode:
                # Starting process failed
                num_errors = num_errors + 1
                logger.error(
                    'Unable to start wpa_supplicant, check debug output')
            else:
                return True
        # Error occurred three times ... should not happen
        logger.error('Error occured multiple times, aborting')
        raise Exception('Unable to start wpa_supplicant')

    @Pyro4.expose
    def status(self):
        if os.path.exists(self._pid):
            return True
        return False

    @Pyro4.expose
    def stop(self):

        if os.path.exists(self._pid):
            logger.info('Stopping wpa_supplicant service')
            with open(self._pid, 'r') as f:
                pid = int(f.read())

            # Stop process and remove PID file
            subprocess.run(['kill', str(pid)], check=True)
            # subprocess.run(['rm', self._pid], check=True)
