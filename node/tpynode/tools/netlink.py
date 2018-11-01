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
# File:          netlink.py
# Date:          2018-02-08
# Last Modified: 2018-10-31
#

import math
import struct
from collections import OrderedDict
import logging
import re
import subprocess

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

NLA_ATTR_BYTE_ALIGN = 4


class NLParseError(Exception):
    """Error in NL Attribute Parser.
    """
    pass


def call_nl_vendor_cmd(nlcmd, request, policy, iface):
    logger.info('Calling NL vendor command %s.' % nlcmd)
    nla_request = nl_encode(request, policy)
    cmd2 = ['iw', 'dev', iface, 'vendor', 'recv', '0x001374', nlcmd, "-"]
    logger.debug('Invoking %s' % ' '.join(cmd2))
    p = subprocess.Popen(cmd2,
                         stdin=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    try:
        [pout, perr] = p.communicate(nla_request, timeout=2)
        if p.returncode:
            logger.error('Could not execute vendor command, cmd failed')
            logger.error(perr.decode())
            raise Exception('Could not complete vendor command')

        nla_stream_bytes = re.findall('[0-9a-fA-F]{2}', pout.decode())
        nla_stream_bytes = bytearray.fromhex(''.join(nla_stream_bytes))

        # Decode the stream
        data = nl_decode(nla_stream_bytes, policy)
        if 'QCA_ATTR_TSF' in data:
            logger.debug('Receiving response with TSF: %s' %
                         data['QCA_ATTR_TSF']['value_raw'])
        else:
            logger.debug('Receiving no response')
        return data

    except subprocess.TimeoutExpired as e:
        p.kill()
        logger.error('Could not execute vendor command, timeout expired')
        raise(e)


def nl_decode(nla, policy):
    """NL Decode.

    Args:
        nla (bytearray): Coded NLA Stream
        policy (dict): NLA Policy definition

    Returns:
        dict: Decoded NLA

    Raises:
        EnvironmentError: In case of implementation errors (don't be afraid)

    """
    nla_parsed = OrderedDict()
    ptr = 0

    # Iterate over nla to find all attributes
    while ptr < len(nla):

        # Extract the current nla header
        cur_hdr = struct.unpack_from('HH', nla, offset=ptr)
        cur_attr_type = cur_hdr[1]
        cur_attr_len = cur_hdr[0]
        cur_attr_payload = nla[ptr + 4: ptr + cur_attr_len]

        if not len(cur_attr_payload) == (cur_attr_len - 4):
            raise EnvironmentError('Payload Length Check failed, \
                this should not happen')

        # Detect Attribute Type
        matched_policies =\
            [key for key, value in policy.items()
                if ('nla_type' not in value or
                    value['nla_type'] == cur_attr_type) and
                   ('nla_len' not in value or
                    value['nla_len'] == cur_attr_len - 4)]

        if not matched_policies:
            print('Unmatched type found %d' % cur_attr_type)

        else:
            cur_attr_key = matched_policies[0]
            cur_attr = policy[cur_attr_key].copy()
            cur_attr.pop('nested', None)
            cur_attr['nla_type'] = cur_attr_type
            cur_attr['nla_len'] = cur_attr_len - 4

            # Check the data type to encode according to policy
            if cur_attr['data_type'] == 'NLA_U8':
                cur_attr_value =\
                    struct.unpack_from('B', nla, offset=(ptr + 4))[0]
                cur_attr_value_raw = nla[ptr + 4: ptr + 5]
                cur_attr_value_raw.reverse()
                cur_attr_value_raw =\
                    "".join("%02x" % b for b in cur_attr_value_raw)
            elif cur_attr['data_type'] == 'NLA_U16':
                cur_attr_value =\
                    struct.unpack_from('H', nla, offset=(ptr + 4))[0]
                cur_attr_value_raw = nla[ptr + 4: ptr + 6]
                cur_attr_value_raw.reverse()
                cur_attr_value_raw =\
                    "".join("%02x" % b for b in cur_attr_value_raw)
            elif cur_attr['data_type'] == 'NLA_U32':
                cur_attr_value =\
                    struct.unpack_from('I', nla, offset=(ptr + 4))[0]
                cur_attr_value_raw = nla[ptr + 4: ptr + 8]
                cur_attr_value_raw.reverse()
                cur_attr_value_raw =\
                    "".join("%02x" % b for b in cur_attr_value_raw)
            elif cur_attr['data_type'] == 'NLA_U64':
                cur_attr_value =\
                    struct.unpack_from('Q', nla, offset=(ptr + 4))[0]
                cur_attr_value_raw = nla[ptr + 4: ptr + 12]
                cur_attr_value_raw.reverse()
                cur_attr_value_raw =\
                    "".join("%02x" % b for b in cur_attr_value_raw)
            elif cur_attr['data_type'] == 'NLA_NESTED':
                    cur_attr_value = nl_decode(
                        cur_attr_payload, policy[cur_attr_key]['nested'])
                    cur_attr_value_raw = None
            else:
                raise NLParseError('Unsupported Datatype detected')

            # Append current attr to list
            cur_attr['value'] = cur_attr_value
            cur_attr['value_raw'] = cur_attr_value_raw
            nla_parsed[cur_attr_key] = cur_attr

        # Set pointer to next attribute and align to 4 bytes
        b = NLA_ATTR_BYTE_ALIGN
        ptr = ptr + b * math.ceil(cur_attr_len / b)

    return nla_parsed


def nl_encode(dataset, policy):
    """NL Encode.

    Converts a nla_data to NetLink Attribute Stream according to policy
    """
    nla_stream = bytearray()

    # Iterate over all elements in nla_struct
    for cur_key, cur_val in dataset.items():

        try:

            if not (type(cur_val) is dict or type(cur_val) is OrderedDict):
                cur_val = {'value': cur_val}

            # Check for matching policy
            mpolicies =\
                [pol_val for pol_key, pol_val in policy.items() if
                    (pol_key == cur_key) and
                    ('nla_type' not in pol_val or 'nla_type' not in cur_val or
                     cur_val['nla_type'] == pol_val['nla_type']) and
                    ('nla_len' not in pol_val or 'nla_len' not in cur_val or
                     cur_val['nla_len'] == pol_val['nla_len'])]

            exp_attr = mpolicies[0].copy()
            exp_attr.update(cur_val)

            # TODO: Check for all variables available

            if exp_attr['data_type'] == 'NLA_U8':
                attr_enc =\
                    struct.pack('HHB', exp_attr['nla_len'] + 4,
                                exp_attr['nla_type'], exp_attr['value'])
            elif exp_attr['data_type'] == 'NLA_U16':
                attr_enc =\
                    struct.pack('HHH', exp_attr['nla_len'] + 4,
                                exp_attr['nla_type'], exp_attr['value'])
            elif exp_attr['data_type'] == 'NLA_U32':
                attr_enc =\
                    struct.pack('HHI', exp_attr['nla_len'] + 4,
                                exp_attr['nla_type'], exp_attr['value'])
            elif exp_attr['data_type'] == 'NLA_U64':
                attr_enc =\
                    struct.pack('HHQ', exp_attr['nla_len'] + 4,
                                exp_attr['nla_type'], exp_attr['value'])
            elif exp_attr['data_type'] == 'NLA_NESTED':
                payload = nl_encode(cur_val, mpolicies[0]['nested'])
                attr_enc =\
                    struct.pack('HH', len(payload) + 4,
                                exp_attr['nla_type'])
                attr_enc = attr_enc + payload
            elif exp_attr['data_type'] == 'NLA_UNSPEC':
                attr_enc =\
                    struct.pack('HH', exp_attr['nla_len'] + 4,
                                exp_attr['nla_type'])
                enc_payload = bytearray(exp_attr['value'].to_bytes(
                    exp_attr['nla_len'], byteorder='little', signed=False))
                attr_enc = attr_enc + enc_payload
            else:
                raise EnvironmentError('Unsupported Data-type detected')

            # Add padding
            b = NLA_ATTR_BYTE_ALIGN
            numpad = math.ceil(len(attr_enc) / b) * b - len(attr_enc)
            attr_enc = bytearray(attr_enc) + bytearray(numpad)

            nla_stream = nla_stream + attr_enc

        except Exception:
            raise Exception('Error parsing attribute %s' % cur_key)

    return nla_stream
