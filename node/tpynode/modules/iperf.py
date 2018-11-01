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
# Last Modified: 2018-10-31

import logging
import subprocess
import os
import json
import Pyro4

from tpynode import TPyModule

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class IPerf(TPyModule):

    def __init__(self, **kwargs):
        super(IPerf, self).__init__(**kwargs)
        self._bin = kwargs.get('bin', 'iperf3')
        self._logfile = kwargs.get('logfile', '/var/log/iperf.log')
        self._process = None
        self._port = kwargs.get('port', None)
        self.killall()

    @Pyro4.expose
    def start_server(self, port=None, *args):
        if self._process is not None:
            logger.warning('Server already started')
            return False
        cmd = [self._bin, '-s']
        if port is None:
            port = self._port
        if port is not None:
            cmd.extend(['-p', str(port)])
        if self._logfile is not None:
            cmd.extend(['--logfile', self._logfile])
        for arg in args:
            cmd.append(arg)
        logger.info('Starting server')
        self._process = subprocess.Popen(cmd)
        return True

    @Pyro4.expose
    def killall(self):
        cmd = ['killall', '-q', os.path.basename(self._bin)]
        subprocess.run(cmd)

    @Pyro4.expose
    def stop_server(self):
        if self._process is None:
            logger.info('Server not running')
            return False
        else:
            self._process.terminate()
            self._process = None
            logger.info('Server stopped')
            return True

    @Pyro4.expose
    def start_client(self, server, port=None, udp=False, bitrate=None,
                     duration=10, omit=None, parallel_connections=None):
        cmd = [self._bin, '-c', server, '--json']
        if port is None:
            port = self._port
        if port is not None:
            cmd.extend(['-p', str(port)])
        if udp is True:
            cmd.append('-u')
        if bitrate is not None:
            cmd.extend(['-b', str(bitrate)])
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        if omit is not None:
            cmd.extend(['-O', str(omit)])
        if parallel_connections is not None:
            cmd.extend(['-P', str(parallel_connections)])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, _ = p.communicate()
        return json.loads(stdout)

    @Pyro4.expose
    def start_client_in_background(self, server, port=None, udp=False,
                                   bitrate=None, duration=10, omit=None,
                                   parallel_connections=None):
        if self._process is not None:
            logger.warning('iPerf already started')
            return False
        cmd = [self._bin, '-c', server, '--json']
        if port is None:
            port = self._port
        if port is not None:
            cmd.extend(['-p', str(port)])
        if udp is True:
            cmd.append('-u')
        if bitrate is not None:
            cmd.extend(['-b', str(bitrate)])
        if duration is not None:
            cmd.extend(['-t', str(duration)])
        if omit is not None:
            cmd.extend(['-O', str(omit)])
        if parallel_connections is not None:
            cmd.extend(['-P', str(parallel_connections)])
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        self._process = p

    @Pyro4.expose
    def wait(self):
        if self._process is None:
            return None
        return self._process.wait()

    @Pyro4.expose
    def get_client_results(self):
        if self._process is None:
            return None
        stdout, _ = self._process.communicate()
        return json.loads(stdout)

