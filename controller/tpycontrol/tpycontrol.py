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

import pkg_resources        # part of setuptools

import logging
from collections import OrderedDict
from tabulate import tabulate

from .devices import Devices
from .tpyremotenode import TPyRemoteNode

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TPyControl:

    def __init__(self, devices, showinfo=True):

        self._nodes = OrderedDict()

        if isinstance(devices, str):
            devices = Devices(devices)

        if type(devices) is Devices:
            devices = devices.get()

        for device in devices:
            # Get properties for node
            hostname = device['host']
            port = int(device['port'])

            # Connect to remote proxy
            try:
                host = TPyRemoteNode(hostname, port)
            except ConnectionError:
                logger.error('Could not connect to {}:{}'.format(hostname, port))
                continue

            self._nodes[device['name']] = host

        if showinfo:
            self.showinfo()

    @property
    def hosts(self):
        return list(self._nodes.values())

    @property
    def nodes(self):
        return self._nodes

    def node(self, which):
        if isinstance(which, int):
            return list(self._nodes.values())[which]
        else:
            return self._nodes[which]

    @property
    def num_nodes(self):
        return len(self._nodes)

    @property
    def version(self):
        return pkg_resources.require("tpycontrol")[0].version

    def get_deviceinfo(self, printable=False):
        info = list()
        for name, node in self._nodes.items():
            node_info = OrderedDict()
            node_info['node'] = name
            node_info['host'] = node.host
            node_info['proxy'] = node.proxy_uri
            node_info['modules (name[:type])'] = self._format_modules(node.modules)
            info.append(node_info)
        info = sorted(info, key=lambda k: k['node'])

        if printable:
            return tabulate(info, headers='keys')
        return info

    @staticmethod
    def _format_modules(modules):
        compact = [name if name == type else '{}:{}'.format(name, type) for (name, type) in modules.items()]
        return ' '.join(compact)

    def showinfo(self):
        print('You are running TPyControl in version %s' % self.version)
        print('Connected to %d remote nodes\n' % self.num_nodes)
        print(self.get_deviceinfo(printable=True))
