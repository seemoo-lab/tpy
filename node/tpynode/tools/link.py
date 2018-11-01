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
# Project:       TPY - The Testbed Experimentation Framework
# Date:          2018-04-06
# Last Modified: 2018-10-31

import logging
import re
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

re_mac = re.compile('^[a-fA-F0-9\:]{17}')


def get_iw_link(iface):
    data = subprocess.check_output(['iw', 'dev', iface, 'link']).decode()
    ddata = data.split('Connected to ')
    links = list()
    for dddata in ddata:
        m = re_mac.match(dddata)
        if m:
            link = dict()
            link['mac'] = m.group()
            link['ssid'] = re.findall('SSID: (.*)', dddata)[0]
            link['freq'] = re.findall('freq: (.*)', dddata)[0]
            link['rx_bytes'], link['rx_pkts'] =\
                re.findall('RX: (\d*) bytes \((\d*) packets\)', dddata)[0]
            link['tx_bytes'], link['tx_pkts'] =\
                re.findall('TX: (\d*) bytes \((\d*) packets\)', dddata)[0]
            link['tx_bitrate'], link['tx_mcs'] =\
                re.findall('tx bitrate: ([\d.]*) .* MCS (\d*)', dddata)[0]
            link['freq'] = re.findall('freq: (.*)', dddata)[0]
            links.append(link)
    return links


def get_iw_station_dump(iface):
    cmd = ['iw', 'dev', iface, 'station', 'dump']
    data = subprocess.check_output(cmd).decode()
    ddata = data.split('Station ')
    stations = list()
    for dddata in ddata:
        m = re_mac.match(dddata)
        if m:
            sta = dict()
            sta['mac'] = m.group()
            sta['rx_bytes'] = int(re.findall('rx bytes:\s+(\d+)', dddata)[0])
            sta['rx_pkts'] = int(re.findall('rx packets:\s+(\d+)', dddata)[0])
            sta['tx_bytes'] = int(re.findall('tx bytes:\s+(\d+)', dddata)[0])
            sta['tx_pkts'] = int(re.findall('tx packets:\s+(\d+)', dddata)[0])
            sta['tx_failed'] = int(re.findall('tx failed:\s+(\d+)', dddata)[0])
            sta['rx_dropped'] =\
                int(re.findall('rx drop misc:\s+(\d+)', dddata)[0])
            sta['signal'] =\
                int(re.findall('signal:\s+([\d.-]+)\s+dBm', dddata)[0])
            sta['tx_bitrate'], sta['tx_mcs'] =\
                re.findall('tx bitrate:\s+([\d.]*) .* MCS (\d+)', dddata)[0]
            sta['rx_bitrate'], sta['rx_mcs'] =\
                re.findall('rx bitrate:\s+([\d.]*) .* MCS (\d+)', dddata)[0]
            stations.append(sta)
    return stations
