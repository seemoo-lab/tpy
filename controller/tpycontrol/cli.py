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
# Date:          2018-04-04

import argparse
import os
import pkg_resources
import sys

from .devices import Devices
from .tpycontrol import TPyControl
from .deploy import deploy_package, restart_nodes, script_nodes


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description='TPy Command Line Utility')
    parser.add_argument('--version', action='store_true', help='show version')

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--verbose", action='store_true', help='verbose info')
    parent_parser.add_argument(
        "-d", "--devices", dest='devices', default='devices.conf',
        type=str, help='devices configuration file')

    subparsers = parser.add_subparsers(help='command')

    # create the parser for the 'list' command
    parser_list = subparsers.add_parser(
        'list', parents=[parent_parser], help='list nodes')
    parser_list.set_defaults(func=cli_list)

    # create the parser for the 'deploy' command
    parser_deploy = subparsers.add_parser(
        'deploy', parents=[parent_parser],
        help='deploys tpynode to all devices')
    parser_deploy.add_argument(
        '-p', '--pkg', dest='pkgfile',
        default=pkg_resources.resource_filename(
            __name__, 'data/tpynode-latest.tar.gz'),
        type=str, help='tpynode distribution package')
    parser_deploy.set_defaults(func=cli_deploy)

    # create the parser for the 'restart' command
    parser_restart = subparsers.add_parser(
        'restart', parents=[parent_parser],
        help='restarts tpynode on all devices')
    parser_restart.set_defaults(func=cli_restart)

    # create the parser for the 'script' command
    parser_script = subparsers.add_parser(
        'script', parents=[parent_parser],
        help='runs a external script for all tpy devices')
    parser_script.add_argument(
        '-s', '--script', dest='scriptfile', required=True,
        default=None, type=str, help='custom script')
    parser_script.set_defaults(func=cli_script)

    args = parser.parse_args(args)
    if 'func' in args:
        args.func(**vars(args))


def cli_list(**kwargs):
    devices = Devices(kwargs.get('devices', None))
    tc = TPyControl(devices.get(), showinfo=False)
    print('Identified %d nodes:' % tc.num_nodes)
    print(tc.get_deviceinfo(printable=True))


def cli_deploy(**kwargs):
    pkg_file = kwargs.get('pkgfile', None)
    devices = Devices(kwargs.get('devices', None))
    deploy_package(devices.get(), pkg_file)


def cli_restart(**kwargs):
    devices = Devices(kwargs.get('devices', None))
    restart_nodes(devices.get())


def cli_script(**kwargs):
    devices = Devices(kwargs.get('devices', None))
    custom_script = kwargs.get('scriptfile', None)
    custom_script = os.path.abspath(custom_script) if custom_script else None
    script_nodes(devices.get(), custom_script)


if __name__ == "__main__":
    main()
