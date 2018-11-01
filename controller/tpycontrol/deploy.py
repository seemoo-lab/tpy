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

import os.path
import time
import subprocess


def deploy_package(devices, file, timeout=None):

    def remote_tmp_dir(dev):
        if dev.get('chroot') is None:
            return os.path.join(dev['tmpdir'], '')
        else:
            return os.path.join(dev['chroot'], dev['tmpdir'].strip('/'), '')

    print('Distributing Installation Package ...')
    cmds = [['scp', '-o', 'StrictHostKeyChecking=no', file,
             'root@%s:%s' % (dev['host'], remote_tmp_dir(dev))]
            for dev in devices]

    run_parallel(cmds, timeout)

    def install_cmd(dev):
        remote_file = os.path.join(dev['tmpdir'], os.path.basename(file))
        if dev.get('chroot') is None:
            return ['ssh', 'root@%s' % dev['host'], '-o',
                    'StrictHostKeyChecking=no',
                    'pip3', 'install', remote_file,
                    '--upgrade', '--no-cache', '-v']
        else:
            return ['ssh', 'root@%s' % dev['host'], '-o',
                    'StrictHostKeyChecking=no',
                    'chroot', dev['chroot'], '/bin/bash', '-c',
                    '"pip3 install {} --upgrade --no-cache -v"'.format(remote_file)]

    print('Installing %s ...' % file)
    cmds = [install_cmd(dev) for dev in devices]
    run_parallel(cmds, None)


def restart_nodes(devices, timeout=10):
    print('Restarting TPyNode ...')

    def restart_cmd(dev):
        cmd = ['ssh', 'root@%s' % dev['host'],
               '-o', 'StrictHostKeyChecking=no',
               'tpynode', 'restart']
        if dev.get('conf') is not None:
            cmd.extend(['-c', dev['conf']])
        return cmd
    cmds = [restart_cmd(dev) for dev in devices]
    run_parallel(cmds, timeout)


def script_nodes(devices, script, timeout=None):
    print('Running Custom Node Script ...')
    cmds = [[script, str(dev['host'])] for dev in devices]
    run_parallel(cmds, timeout)


def run_parallel(cmds, timeout=None):
    processes = [subprocess.Popen(cmd) for cmd in cmds]
    tic = time.time()
    while timeout is None or time.time() < (tic + timeout):
        failed_processes = [p for p in processes
                            if p.poll() is not None and p.poll() != 0]
        if failed_processes:
            for p in processes:
                p.terminate()
            raise Exception('Unable to execute %s' %
                            ' '.join(failed_processes[0].args))
        if all(p.poll() == 0 for p in processes):
            return True
    for p in processes:
        p.terminate()
    raise TimeoutError('Processing commands timed out')
