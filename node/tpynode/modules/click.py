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
import time
import socket
import os
import Pyro4

from tpynode import TPyModule

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Click(TPyModule):

    def __init__(self, **kwargs):
        super(Click, self).__init__(**kwargs)
        self._bin = kwargs.get('bin', 'click')
        self._config = kwargs.get('config', '')
        self._logfile = kwargs.get('logfile', None)
        self._socket_port = int(kwargs.get('socket_port', 7777))
        self._socket_recv_buffer = kwargs.get('socket_recv_buffer', 65536)
        self._socket = None
        self._process = None
        self.killall()

    @Pyro4.expose
    def start(self, *args):
        if self._process is not None:
            if self._process.poll() is not None:
                self.stop()
            else:
                logger.info('Click instance already started')
                return

        cmd = [self._bin]
        if self._socket_port is not None:
            cmd.append('port={}'.format(self._socket_port))
        for arg in args:
            cmd.append(arg)
        cmd.append(self._config)
        if self._logfile is None:
            self._process = subprocess.Popen(cmd)
        else:
            self._process = subprocess.Popen(cmd, stdout=open(self._logfile, 'w'), stderr=subprocess.STDOUT)
        logger.info('Click instance started: {}'.format(self._process))

    @Pyro4.expose
    def killall(self):
        cmd = ['killall', '-q', os.path.basename(self._bin)]
        subprocess.run(cmd)

    @Pyro4.expose
    def stop(self):
        if self._process is not None:
            self._process.terminate()
            logger.info('Click instance stopped')
        self._process = None
        # Make sure that tun device is free
        time.sleep(1)

    @Pyro4.expose
    def restart(self):
        self.stop()
        self.start()

    def _socket_cmd(self, cmd):
        if self._socket is None:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect(('localhost', self._socket_port))
            recv = self._socket.recv(self._socket_recv_buffer).decode('ascii')  # read Click::ControlSocket header
            logger.debug('Connected to Click socket: {}'.format(recv))
        self._socket.send(cmd.encode('ascii'))
        recv = self._socket.recv(self._socket_recv_buffer).decode('ascii').split('\r\n', 2)
        return recv

    @Pyro4.expose
    def socket_read(self, element):
        cmd = 'READ {}\n'.format(element)
        return self._socket_cmd(cmd)

    @Pyro4.expose
    def socket_write(self, element, data):
        cmd = 'WRITE {} {}\n'.format(element, data)
        return self._socket_cmd(cmd)

    @Pyro4.expose
    def socket_write_batch(self, element_data_pairs):
        return [self.socket_write(e[0], e[1]) for e in element_data_pairs]
