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
# Date:          2018-03-20
# Last Modified: 2018-10-31

import argparse
import configparser
import inspect
import logging
import pkg_resources
import Pyro4
import sys
import os
import signal
import time

from daemonize import Daemonize
from pluginbase import PluginBase
from tabulate import tabulate

from .tpynode import TPyNode
import tpynode.modules

# -----------------------------------------------------------------------------
# --- Settings ----------------------------------------------------------------
# -----------------------------------------------------------------------------

sys.excepthook = Pyro4.util.excepthook
cfgfile_default = '/etc/tpynode.conf'

# -----------------------------------------------------------------------------
# --- Logger Settings ---------------------------------------------------------
# -----------------------------------------------------------------------------

log_format = '%(asctime)s %(levelname)-5s %(message)s'
log_level = logging.INFO

formatter = logging.Formatter(log_format)
logging.basicConfig(level=log_level,
                    format=log_format)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)


# -----------------------------------------------------------------------------
# --- Functions ---------------------------------------------------------------
# -----------------------------------------------------------------------------

def load_external_modules(module_path, base_type=object):

    if not module_path:
        logger.info('Skipping loading external modules')
        return list()

    logger.info('Loading external modules from %s' % (module_path))
    pluginbase = PluginBase(package='modules_ext')
    plugin_source = pluginbase.make_plugin_source(searchpath=[module_path],
                                                  persist=True,
                                                  identifier='tpymodules')
    modules = list()

    # Find the Plugins
    for plugin_module in plugin_source.list_plugins():

        # Try to load the plugin
        try:
            plugin = plugin_source.load_plugin(plugin_module)
            plugin_classes = inspect.getmembers(plugin, inspect.isclass)

            # Check the classes in the plugin
            for plugin_class in plugin_classes:

                # Only scan local classes
                if plugin_class[1].__module__ == plugin.__name__:

                    # Check base type
                    if issubclass(plugin_class[1], base_type):

                        module_name = plugin_class[0]
                        module = plugin_class[1]
                        module_file = os.path.basename(plugin.__file__)   
                        logger.info('Importing external module %s from %s' % (module_name, module_file))
                        module.__file__ = plugin.__file__
                        module.__plugin__ = True

                        # Add this module
                        modules.append(module)
        except Exception as e:
            logger.error('Unable to load external modules from %s, import failed' % plugin_module)
            # ToDo: Real parsing here
            logger.exception(e)
    return modules


def load_internal_modules(base_type=object):

    # Find internal modules
    modules = list()
    int_modules = inspect.getmembers(tpynode.modules, inspect.isclass)
    for module_class in int_modules:
        module = module_class[1]
        if issubclass(module, base_type):
            logger.info('Using internal module %s' % module.__name__)
            module.__plugin__ = False
            modules.append(module)
    return modules


def load_modules(ext_module_path, base_type=object):
    modules = load_internal_modules(base_type)
    modules.extend(load_external_modules(ext_module_path, base_type))
    return modules


def get_module_by_name(modules, name):
    for module in modules:
        if module.__name__ == name:
            return module
    return None


# -----------------------------------------------------------------------------
# --- Daemon ------------------------------------------------------------------
# -----------------------------------------------------------------------------

def run_tpynode(config, modules):

    tpy_config = config['TPyNode']
    host = tpy_config.get('host', 'localhost')
    port = int(tpy_config.get('port', '42337'))
    token = tpy_config.get('token', None)   # Not used yet

    setattr(Pyro4.config, 'HOST', host)

    # Start the Pyro Daemon
    pyro = Pyro4.Daemon(port=port)
    tpynode = TPyNode(pyro=pyro)
    uri = pyro.register(tpynode, 'tpynode')
    if not uri:
        raise Exception('Unable to register TPyHost in daemon service.')
    logger.info('Registered TPyHost instance at %s' % uri)

    # Register modules ...
    modulecfg = [{**dict(config.items(k)), **{'name': k}}
                 for k in config.keys() if k != 'TPyNode' and
                 k != 'DEFAULT']
    for mcfg in modulecfg:
        if mcfg.get('module') is None:
            mcfg['module'] = mcfg['name']
        logger.info('Exposing module %s as %s' % (mcfg['module'],
                                                  mcfg['name']))
        module = get_module_by_name(modules, mcfg['module'])(**mcfg)
        uri = pyro.register(module, mcfg['name'])
        if not uri:
            raise Exception('Unable to register module %s in daemon service.' % mcfg['name'])
        logger.info('Registered %s Module instance at %s' % (mcfg['module'], uri))
        tpynode.register_module(mcfg['module'], mcfg['name'])

    logger.info('Awaiting incoming Connections ...')
    pyro.requestLoop()


# -----------------------------------------------------------------------------
# --- MAIN --------------------------------------------------------------------
# -----------------------------------------------------------------------------

def main():

    # Initialize argument parser
    parser = argparse.ArgumentParser(description='TPyNode Daemon')
    parser.add_argument('--version', action='version', help='show version',
                        version=pkg_resources.require("tpynode")[0].version)

    parser.add_argument('cmd', action='store', help='operation mode',
                        nargs='?', choices=['start', 'stop', 'restart', 'run',
                        'modules', 'info'],
                        default='run')

    parser.add_argument(
        "-c", "--conf", dest='cfgfile', default=cfgfile_default,
        type=str, help='configuration file')

    # Parse Command Line Arguments
    args = parser.parse_args(sys.argv[1:])

    # Load the configuration file
    config = configparser.ConfigParser()
    logger.info('Loading configuration from %s' % args.cfgfile)
    if not config.read(args.cfgfile) or 'TPyNode' not in config.sections():
        logger.error('Unable to parse configuration, please check file')
        sys.exit(1)

    ext_module_path = config['TPyNode'].get('module_path')
    modules = load_modules(ext_module_path)

    def run():
        logger.info('Running TPyNode')
        run_tpynode(config, modules)

    def start():
        logger.info('Starting TPyNode in Daemon Mode')

        pidfile = config['TPyNode'].get('pidfile')

        def runner():
            run_tpynode(config, modules)

        daemon = Daemonize(app="tpynode", pid=pidfile, action=runner)
        daemon.start()

    def stop():
        logger.info('Stopping TPyNode Daemon')
        try:
            pidfile = config['TPyNode'].get('pidfile')
            with open(pidfile) as pid:
                os.kill(int(pid.read()), signal.SIGTERM)
                time.sleep(1)  # make sure that pid file is released
        except FileNotFoundError:
            logger.info('No running instance found')

    def restart():
        stop()
        start()

    def list_modules():
        # list all modules
        module_info = list()
        for m in modules:
            module_name = m.__name__
            module_desc = m.__doc__
            module_desc = ' '.join([str.strip() for str in  module_desc.splitlines()]) if module_desc else ''
            module_base = m.__base__.__name__
            module_file = os.path.basename(m.__file__) if m.__plugin__ else 'builtin'

            module_info.append({
                'Name': module_name,
                'Base': module_base,
                'Definition': module_file,
                'Description': module_desc})

        print('Available Modules:')
        print(tabulate(module_info, headers='keys'))

    def info():
        logger.error('Not yet implemented')

    cmd_map = {
        'run': run,
        'start': start,
        'stop': stop,
        'restart': restart,
        'modules': list_modules,
        'info': info,
    }

    cmd_map[args.cmd]()
    sys.exit(0)


if __name__ == "__main__":
    main()
