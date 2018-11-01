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

import os
import Pyro4
import re
import struct
import subprocess

from .wifiinterface import WiFiInterface

rx_mbox = re.compile((
    '\s+\[\s?([0-9a-f]+)\].*0x[0-9a-f]{8}\s->\s[0-9a-f\s]{17}\n(\s{3}.*\n)?'))

rx_stations1 = re.compile((
    '\[(\d)\]\s+([0-9a-fA-F:]{17})\s+([a-zA-Z]+)\s+AID'
    '\s+(\d)(\n[^\[].*total.*)?(\n[^\[].*)?(\n[^\[].*)?'),
    re.MULTILINE)
rx_stations2 = re.compile((
    '.*?\(\[(\d+)\].*?total\s+(\d+)\s+drop\s+(\d+)\s+'
    '\(dup\s+(\d+).+?old\s+(\d+)'))
rx_stations3 = re.compile((
    'Rx\sinvalid\sframe\:\s+non-data\s(\d+).*(\d+).*'
    '(\d+).+replay\s+(\d+)'))
rx_stations4 = re.compile((
    'Rx\/MCS\:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
    '\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
    '\s+(\d+)\s+(\d+)'))

rx_fw_version = re.compile('(\d+\.\d+\.\d+\.\d+)')


def mac_addr_to_bytearray(addr):
    """Convert MAC Address to Bytearray

    Args:
        addr (String): MAC Address

    Returns:
        Bytearray: Byte Representation of MAC Addr

    Raises:
        AttributeError: Description
    """
    rx = re.compile('([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:' +
                    '([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:([0-9a-fA-F]+)')
    if not rx.match(addr):
        raise AttributeError('Not a valid MAC Address %s' % addr)
    addr_exp = rx.findall(addr)[0]
    addr_hex = struct.pack(
        "BBBBBB", int(addr_exp[0], 16),
        int(addr_exp[1], 16), int(addr_exp[2], 16),
        int(addr_exp[3], 16), int(addr_exp[4], 16),
        int(addr_exp[5], 16))
    return bytearray(addr_hex)


class DebugFS (WiFiInterface):

    """DebugFS Module.
    Provides access to an IEEE 802.11 interface debugFS.
    """

    def __init__(self, **kwargs):
        super(DebugFS, self).__init__(**kwargs)

    @property
    def debugfs_path(self):
        if hasattr(self, '_debugfs_path') and self._debugfs_path:
            return self._debugfs_path
        else:
            rx = re.compile('debugfs\\s+on\\s+(.+)\\s+type\\s+debugfs')
            mounts = subprocess.check_output(['mount']).decode()
            rootpath = rx.findall(mounts)[0]
            self._debugfs_path = os.path.join(
                rootpath, 'ieee80211', 'phy%d' % self.get_phy_id())
            return self._debugfs_path

    @Pyro4.expose
    def read_debugfs(self, debugfs):
        filepath = os.path.join(self.debugfs_path, debugfs)
        if not os.path.isfile(filepath):
            self.logger.error('Unable to read file %s' % filepath)
            return
        with open(filepath, mode='r') as file:
            data = file.read()
        return data

    @Pyro4.expose
    def write_debugfs(self, debugfs, data):
        filemode = 'w' if isinstance(data, str) else 'wb'
        filepath = os.path.join(self.debugfs_path, debugfs)
        with open(filepath, filemode) as file:
            r = file.write(data)
        return r

    @Pyro4.expose
    def get_bf(self):
        data = self.read_debugfs('wil6210/bf')

        for seg in data.split('CID'):
            results = list()
            m = re.findall('\s*(\d+)\s*\{', seg)
            if m:
                r = dict()
                r['cid'] = m[0]
                r['tsf'] = re.findall('TSF\s+=\s+(0x[0-9a-fA-F]+)', seg)[0]
                r['tx_mcs'] = re.findall('TxMCS\s+=\s+(\d+)', seg)[0]
                r['tx_tpt'] = re.findall('TxTpt\s+=\s+(\d+)', seg)[0]
                r['sqi'] = re.findall('SQI\s+=\s+(\d+)', seg)[0]
                r['rssi'] = re.findall('RSSI\s+=\s+(-?\d+)', seg)[0]
                r['status_code'], r['status'] =\
                    re.findall('Status\s+=\s+(0x[0-9a-fA-F]+)\s(\w+)', seg)[0]
                r['rx_sector'], r['tx_sector'] =\
                    re.findall('Sectors.*my\s+(\d+)\:\s*(\d+)', seg)[0]
                r['rx_sector_peer'], r['tx_sector_peer'] =\
                    re.findall('Sectors.*peer\s+(\d+)\:\s*(\d+)', seg)[0]
                r['rx_goodput'], r['tx_goodput'] =\
                    re.findall('Goodput\(rx\:tx\)\s+(\d+)\:\s*(\d+)', seg)[0]
                results.append(r)
        return results

    @Pyro4.expose
    def get_wmi_mbox(self):
        if not self.debugfs_path:
            return None

        data = self.read_debugfs('wil6210/mbox')
        mbox = {'ring_tx': list(), 'ring_rx': list()}

        ring_tx = data.split('ring rx = ')[0]
        ring_rx = data.split('ring rx = ')[1]

        ring_rx_entries = re.split('\[.{2}\]', ring_rx)[1:]
        for entry in ring_rx_entries:
            entry_lines = entry.splitlines()
            entry_data = ''.join(entry_lines[1:])
            entry_data = ''.join(re.findall('[0-9a-fA-F]{2}', entry_data))
            if len(entry_data) > 0:
                entry_bytes = bytearray.fromhex(entry_data)
                evt_id = struct.unpack_from('B B H I', entry_bytes)[2]
                evt_data = entry_bytes[8:]

                mbox['ring_rx'].append({'id': evt_id, 'data': evt_data})

        ring_tx_entries = re.split('\[.{2}\]', ring_tx)[1:]
        for entry in ring_tx_entries:
            entry_lines = entry.splitlines()
            entry_data = ''.join(entry_lines[1:])
            entry_data = ''.join(re.findall('[0-9a-fA-F]{2}', entry_data))
            if len(entry_data) > 0:
                entry_bytes = bytearray.fromhex(entry_data)
                cmd_id = struct.unpack_from('B B H I', entry_bytes)[2]
                cmd_data = entry_bytes[8:]

                mbox['ring_tx'].append({'id': cmd_id, 'data': cmd_data})
        return mbox

    @Pyro4.expose
    def get_fw_version(self):
        data = self.read_debugfs('wil6210/fw_version')
        m = rx_fw_version.findall(data)[0]
        return m

    @Pyro4.expose
    def get_debugfs_hw_version(self):
        data = self.read_debugfs('wil6210/hw_version')
        return int(data, 16)

    @Pyro4.expose
    def get_recovery(self):
        data = self.read_debugfs('wil6210/recovery')
        mode = re.findall('mode\s+=\s+(\S+)', data)
        mode = mode[0] if mode else 'unknown'
        state = re.findall('state\s+=\s+(\S+)', data)
        state = state[0] if state else 'unknown'
        return {'mode': mode, 'state': state}

    @Pyro4.expose
    def get_recovery_count(self):
        data = self.read_debugfs('wil6210/recovery_count')
        c = int(data) if data else -1
        return c

    @Pyro4.expose
    def get_debug_stations(self):
        data = self.read_debugfs('wil6210/stations')
        results = list()
        mcs_zero = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        stations_dump = rx_stations1.findall(data)

        for sta in stations_dump:
            dump2 = rx_stations2.findall(sta[4])
            dump3 = rx_stations3.findall(sta[5])
            dump4 = rx_stations4.findall(sta[6])
            cid = sta[0]
            r = {
                'cid': cid,
                'mac': sta[1],
                'status': sta[2],
                'aid': sta[3],
                'agg_win_size': int(dump2[0][0]) if len(dump2) > 0 else 0,
                'pkts_total': int(dump2[0][1]) if len(dump2) > 0 else -1,
                'pkts_drop': int(dump2[0][2]) if len(dump2) > 0 else -1,
                'pkts_dup': int(dump2[0][3]) if len(dump2) > 0 else -1,
                'pkts_old': int(dump2[0][4]) if len(dump2) > 0 else -1,
                'inv_nondata': int(dump3[0][0]) if len(dump3) > 0 else -1,
                'inv_short': int(dump3[0][1]) if len(dump3) > 0 else -1,
                'inv_large': int(dump3[0][2]) if len(dump3) > 0 else -1,
                'inv_replay': int(dump3[0][3]) if len(dump3) > 0 else -1,
                'rx_mcs': list(map(int, dump4[0])) if len(dump4) > 0
                else mcs_zero}

            # Run some checks
            if r['status'] == 'connected':
                # Check for extensive information, should be there ...
                if not (len(dump3) > 0 and len(dump4) > 0):
                    self.logger.error(('Error parsing extended information '
                                       'for connected station in debugFS.'))
            elif r['status'] == 'unused':
                if len(dump2) > 0 or len(dump3) > 0 or len(dump4) > 0:
                    self.logger.error(('Error parsing extended information '
                                       'for unused station in debugFS.'))
            elif r['status'] == 'unknown':
                pass
            elif r['status'] == 'pending':
                pass
            else:
                self.logger.error((
                    'Invalid status \'%s\' in parsing '
                    'stations debugFS register.' % r['Status']))
            results.append(r)
        return results

    @Pyro4.expose
    def get_fw_status(self):
        data = self.read_debugfs('wil6210/status[0]')
        if len(data) == 0:
            return 0
        return int(data, 16)

    @Pyro4.expose
    def get_sweep_dump(self):
        data = self.read_debugfs('wil6210/sweep_dump')
        sweepinfo = list()
        for swp_data in re.findall('\[.*\]', data):
            swp = dict()
            swp['id'] = int(re.findall('\[\s*(\d+)', swp_data)[0])
            swp['src'] = re.findall('src:\s+([0-9a-fA-F:]{17})', swp_data)[0]
            swp['sec'] = int(re.findall('sec:\s+(\d+)', swp_data)[0])
            swp['cdown'] = int(re.findall('cdown:\s+(\d+)', swp_data)[0])
            swp['initiator'] = not bool(re.findall('dir:\s+(\d)', swp_data)[0])
            swp['snr'] = float(re.findall('snr:\s+(-?\d+.\d+)\sdB', swp_data)[0])
            swp['snr_raw'] = re.findall('snr:.*\((0x[0-9a-fA-F:]+)\)', swp_data)[0]
            if swp['src'] != '00:00:00:00:00:00':
                sweepinfo.append(swp)
        return sweepinfo

    @Pyro4.expose
    def get_debugfs_temp(self):
        data = self.read_debugfs('wil6210/temp')
        if data == 'Failed':
            return {'mac': -1, 'radio': -1}
        t_mac = re.findall('T_mac\s+=\s+(\d+.\d+)', data)
        t_mac = float(t_mac[0]) if t_mac else 0
        t_rad = re.findall('T_radio\s+=\s+(\d+.\d+)', data)
        t_rad = float(t_rad[0]) if t_rad else 0
        return {'mac': t_mac, 'radio': t_rad}

    @Pyro4.expose
    def send_mgmt_frame(self, ftype, dst, src, bss, payload):
        """Send a management frame through the debugfs.

        Args:
            ftype (Int): Frame Type
            dst (String): Destination MAC Address
            src (String): Source MAC Address
            bss (String): BSS MAC Address
            payload (TYPE): Payload

        Returns:
            TYPE: Description
        """
        frame = bytearray(struct.pack('H', ftype))
        frame.extend(bytearray.fromhex('b907'))
        frame.extend(mac_addr_to_bytearray(dst))
        frame.extend(mac_addr_to_bytearray(src))
        frame.extend(mac_addr_to_bytearray(bss))
        frame.extend(bytearray(2))
        frame.extend(payload)
        return self.write_debugfs('wil6210/tx_mgmt', frame)

    @Pyro4.expose
    def send_wmi(self, cmd_id, payload):
        data = bytearray(struct.pack('H H I', 0, cmd_id, 0))
        if type(payload) is str:
            data.extend(payload.encode())
        else:
            data.extend(payload)
        self.write_debugfs('wil6210/wmi_send', data)
