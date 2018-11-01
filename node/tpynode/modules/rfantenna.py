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
# Date:          2018-07-17
# Last Modified: 2018-07-17

import Pyro4

from tpynode.tools.rfantenna import rfantenna


class RFAntenna():

    @Pyro4.expose
    def get_rf_selected_tx_sector(self, peer):
        return rfantenna.get_selected_sector(self.iface, 0x01, peer)

    @Pyro4.expose
    def get_rf_selected_rx_sector(self, peer):
        return rfantenna.get_selected_sector(self.iface, 0x00, peer)

    @Pyro4.expose
    def set_rf_selected_tx_sector(self, peer, sector):
        return rfantenna.set_selected_sector(self.iface, 0x01, peer, sector)

    @Pyro4.expose
    def set_rf_selected_rx_sector(self, peer, sector):
        return rfantenna.set_selected_sector(self.iface, 0x00, peer, sector)

    @Pyro4.expose
    def get_rf_tx_sector_config_raw(self, sector):
        return rfantenna.get_sector_config(self.iface, 0x01, sector)

    @Pyro4.expose
    def get_rf_rx_sector_config_raw(self, sector):
        return rfantenna.get_sector_config(self.iface, 0x00, sector)

    @Pyro4.expose
    def set_rf_tx_sector_config_raw(self, sector, *args):
        return rfantenna.set_sector_config(self.iface, 0x01, sector, *args)

    @Pyro4.expose
    def set_rf_rx_sector_config_raw(self, sector, *args):
        return rfantenna.set_sector_config(self.iface, 0x00, sector, *args)

    @Pyro4.expose
    def get_rf_tx_sector_config(self, sector):
        cfg = self.get_rf_tx_sector_config_raw(sector)
        return rfantenna.decode_sector_config(*cfg)

    @Pyro4.expose
    def set_rf_tx_sector_config(self, sector, definition):
        cfg = rfantenna.encode_sector_config(definition)
        self.set_rf_tx_sector_config_raw(sector, *cfg)

    @Pyro4.expose
    def get_rf_rx_sector_config(self, sector):
        cfg = self.get_rf_rx_sector_config_raw(sector)
        return rfantenna.decode_sector_config(*cfg)

    @Pyro4.expose
    def set_rf_rx_sector_config(self, sector, definition):
        cfg = rfantenna.encode_sector_config(definition)
        self.set_rf_rx_sector_config_raw(sector, *cfg)

    @Pyro4.expose
    def get_rf_tx_sector_codebook(self, max_sectors=64, ignore_invalid=True):
        codebook = list()
        for s in range(0, max_sectors):
            data = self.get_rf_tx_sector_config(s)
            if ignore_invalid:
                if data['dtype'] == ([0] * 8) and data['etype'] == [0] * 32:
                    continue
            data['sid'] = s
            codebook.append(data)
        return codebook

    @Pyro4.expose
    def set_rf_tx_sector_codebook(self, codebook):
        for sector in codebook:
            self.set_rf_tx_sector_config(sector['sid'], sector)
