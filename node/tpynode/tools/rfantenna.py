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
# File:          rfantenna.py
# Date:          2018-02-07
# Last Modified: 2018-10-31
#

import json
import pkg_resources
import time
import logging
from collections import OrderedDict

from .netlink import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


def mac_addr_to_int(addr):
    """Convert MAC Address to Integer.

    Args:
        addr (String): MAC Address

    Returns:
        Integer: Integer Representation of MAC Address
    """
    mac = mac_addr_to_bytearray(addr)
    return int.from_bytes(mac, 'little')


def get_rf_default_nl_attr_policy():
    policy = pkg_resources.resource_string(
        __name__, '../data/wil_rf_sector_policy.json')
    return json.loads(policy.decode())


class rfantenna(object):

    RF_SECTOR_TYPE_RX = 0x00
    RF_SECTOR_TYPE_TX = 0x01

    ANT_SECTOR_MAX = 64

    QCA_VENDOR_SUBCMD_DMG_RF_GET_SECTOR_CFG = "0x8b"
    QCA_VENDOR_SUBCMD_DMG_RF_SET_SECTOR_CFG = "0x8c"
    QCA_VENDOR_SUBCMD_DMG_RF_GET_SELECTED_SECTOR = "0x8d"
    QCA_VENDOR_SUBCMD_DMG_RF_SET_SELECTED_SECTOR = "0x8e"

    _nl_policy = get_rf_default_nl_attr_policy()

    def __init__(self):
        pass

    @classmethod
    def get_selected_sector(cls, iface, sector_type, peer_addr):
        """Get selected sector from NL vendor commands.

        Provides access to low level API
        """
        logger.debug('get rf selected sector')
        tic = time.time()

        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_MAC_ADDR'] = mac_addr_to_int(peer_addr)

        # Call the vendor command
        vendor_cmd = cls.QCA_VENDOR_SUBCMD_DMG_RF_GET_SELECTED_SECTOR
        response = call_nl_vendor_cmd(vendor_cmd, request, cls._nl_policy,
                                      iface)

        toc = time.time() - tic
        logger.debug('get rf selected sector completed in %.2f seconds'
                     % toc)

        # Extract Sector ID from Response
        return response['QCA_ATTR_DMG_RF_SECTOR_INDEX']['value']

    @classmethod
    def set_selected_sector(cls, iface, sector_type, peer_addr, sector_index):
        """Set selected sector with NL vendor commands.

        Provides access to low level API
        """
        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_MAC_ADDR'] = mac_addr_to_int(peer_addr)
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index

        # Call the vendor command
        vendor_cmd = cls.QCA_VENDOR_SUBCMD_DMG_RF_SET_SELECTED_SECTOR
        call_nl_vendor_cmd(vendor_cmd, request, cls._nl_policy, iface)

    @classmethod
    def get_sector_config(cls, iface, sector_type, sector_index):
        """Get sector config from NL vendor commands.

        Provides access to low level API
        """

        logger.debug('get rf sector config')
        tic = time.time()

        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type
        request['QCA_ATTR_DMG_RF_MODULE_MASK'] = 0x01

        # Call the vendor cmd
        vendor_cmd = cls.QCA_VENDOR_SUBCMD_DMG_RF_GET_SECTOR_CFG
        response = call_nl_vendor_cmd(vendor_cmd, request, cls._nl_policy,
                                      iface)

        # Shorten the results
        shortresp = response['QCA_ATTR_DMG_RF_SECTOR_CFG']['value']
        shortresp = shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_0']['value']

        # results = OrderedDict()
        try:
            # results['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX'] =\
            #     shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX']['value']
            # results['etype0'] =\
            etype0 = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0']['value_raw'],
                16)
            # results['etype1'] =\
            etype1 = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1']['value_raw'],
                16)
            # results['etype2'] =\
            etype2 = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2']['value_raw'],
                16)
            # results['psh_hi'] =\
            psh_hi = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI']['value_raw'],
                16)
            # results['psh_lo'] =\
            psh_lo = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO']['value_raw'],
                16)
            # results['dtype_x16'] =\
            dtype_x16 = int(
                shortresp['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16']['value_raw'],
                16)
        except KeyError:
            print('Key error in get_vendor_sector_cfg, aborting')

        toc = time.time() - tic
        logger.debug('get rf sector config completed in %.2f seconds'
                     % toc)
        return (psh_hi, psh_lo, etype0, etype1, etype2, dtype_x16)

    @classmethod
    def set_sector_config(cls, iface, sector_type, sector_index,
                          psh_hi, psh_lo, etype0, etype1, etype2, dtype_x16):
        """Set sector config with NL vendor commands.

        Provides access to low level API
        """

        # Create the request
        request = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_INDEX'] = sector_index
        request['QCA_ATTR_DMG_RF_SECTOR_TYPE'] = sector_type

        cfg_request = OrderedDict()
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_INDEX'] = 0
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'] = etype0
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'] = etype1
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'] = etype2
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_HI'] = psh_hi
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_PSH_LO'] = psh_lo
        cfg_request['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'] = dtype_x16

        cfg_module_request = OrderedDict()
        cfg_module_request['QCA_ATTR_DMG_RF_SECTOR_CFG_MODULE_0'] = \
            cfg_request

        request['QCA_ATTR_DMG_RF_SECTOR_CFG'] = OrderedDict()
        request['QCA_ATTR_DMG_RF_SECTOR_CFG'] =\
            cfg_module_request

        # Call the vendor cmd
        vendor_cmd = cls.QCA_VENDOR_SUBCMD_DMG_RF_SET_SECTOR_CFG
        call_nl_vendor_cmd(vendor_cmd, request, cls._nl_policy, iface)

    @classmethod
    def extract_psh(cls, psh_hi, psh_lo):
        """Extract PSH value from Query Response

        Args:
            data (DICT): Response

        Returns:
            List: List of 32 PSH values
        """
        # psh_lo = int(psh_lo, 16)
        # psh_hi = int(psh_hi, 16)

        psh = [0] * 32
        for n in range(0, 32):
            if n >= 16:
                psh[n] = (psh_hi & (0x3 << ((n - 16) * 2)))\
                    >> ((n - 16) * 2)
            else:
                psh[n] = (psh_lo & (0x3 << (n * 2))) >> (n * 2)
        return psh

    @classmethod
    def pack_psh(cls, value):
        if not (type(value) is list and len(value) == 32):
            raise AttributeError('Value should be list of 32 elements')

        psh_lo = 0x00
        psh_hi = 0x00

        for n in range(0, 32):
            v = value[n] & 0x3
            if n >= 16:
                psh_hi |= v << (2 * (n - 16))
            else:
                psh_lo |= v << (2 * n)
        return (psh_hi, psh_lo)

    @classmethod
    def extract_etype(cls, etype0, etype1, etype2):
        # # ETYPE Bit0 for all RF chains[31-0] - bit0 of Edge amplifier gain
        # etype0 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE0'], 16)
        # # ETYPE Bit1 for all RF chains[31-0] - bit1 of Edge amplifier gain
        # etype1 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE1'], 16)
        # # ETYPE Bit2 for all RF chains[31-0] - bit2 of Edge amplifier gain
        # etype2 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_ETYPE2'], 16)

        etype = [0] * 32
        for n in range(0, 32):
            etype[n] |= (etype0 >> n) % 2
            etype[n] |= ((etype1 >> n) % 2) << 1
            etype[n] |= ((etype2 >> n) % 2) << 2
        return etype

    @classmethod
    def pack_etype(cls, value):
        if not (type(value) is list and len(value) == 32):
            raise AttributeError('Value should be list of 32 elements')

        etype0 = 0x00
        etype1 = 0x00
        etype2 = 0x00

        for n in range(0, 32):
            v = value[n]
            etype0 |= ((v >> 0) % 2) << n
            etype1 |= ((v >> 1) % 2) << n
            etype2 |= ((v >> 2) % 2) << n

        return (etype0, etype1, etype2)

    @classmethod
    def extract_dtype_x16(cls, dtype_x16):
        # D-Type values (3bits) for 8 Distribution amplifiers + X16 switch bits
        # dtype_x16 = int(data['QCA_ATTR_DMG_RF_SECTOR_CFG_DTYPE_X16'], 16)

        dtypes = [0] * 8
        for n in range(0, 8):
            dtypes[n] = (dtype_x16 & (0x7 << (n * 3))) >> (n * 3)
        x16 = (dtype_x16 & 0xff000000) >> 24
        return (dtypes, x16)

    @classmethod
    def pack_dtype_x16(cls, dtype_value, x16_value):
        if not (type(dtype_value) is list and len(dtype_value) == 8):
            raise AttributeError('DType Value should be list of 8 elements')
        if not (type(x16_value) is int):
            raise AttributeError('X16 Value should be integer')

        dt_x16 = (x16_value & 0xff) << 24

        for n in range(0, 8):
            v = dtype_value[n] & 0x7
            dt_x16 |= v << (n * 3)

        return dt_x16

    @classmethod
    def decode_sector_config(cls, psh_hi, psh_lo, etype0, etype1, etype2,
                             dtype_x16):
        psh = cls.extract_psh(psh_hi, psh_lo)
        etype = cls.extract_etype(etype0, etype1, etype2)
        dtype, x16 = cls.extract_dtype_x16(dtype_x16)
        return {'psh': psh, 'etype': etype, 'dtype': dtype, 'x16': x16}

    @classmethod
    def encode_sector_config(cls, cfg):
        psh_hi, psh_lo = cls.pack_psh(cfg['psh'])
        etype0, etype1, etype2 = cls.pack_etype(cfg['etype'])
        dt_x16 = cls.pack_dtype_x16(cfg['dtype'], cfg['x16'])
        return (psh_hi, psh_lo, etype0, etype1, etype2, dt_x16)
