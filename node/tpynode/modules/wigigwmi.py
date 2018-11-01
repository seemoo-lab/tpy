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

import Pyro4
import struct

from .debugfs import DebugFS, mac_addr_to_bytearray


class WiGigWMI(DebugFS):

    """WiGigWMI Module.
    Provides control over an Wireless IEEE 802.11ad Interface.
    """

    def __init__(self, **kwargs):
        super(WiGigWMI, self).__init__(**kwargs)

    @Pyro4.expose
    def call_wmi(self, cmd_id, payload):
        self.send_wmi(cmd_id, payload)
        responses = self.get_wmi_mbox()['ring_rx']
        self.logger.debug('Received %d event(s) in wmi mbox' % len(responses))
        for r in responses:
            self.logger.debug('rx evt: %s payload %s (%d)', hex(r['id']),
                              r['data'].hex(), len(r['data']))
        return responses

    WMI_ECHO_CMDID = 0x803
    WMI_ECHO_RSP_EVENTID = 0x1803

    @Pyro4.expose
    def wmi_echo(self, payload):
        evt = self.call_wmi(self.WMI_ECHO_CMDID, payload)[0]
        if evt['id'] == 0x1803:
            if type(payload) is str:
                return evt['data'].decode()
            else:
                return evt['data']
        return None

    WMI_RS_CFG_CMDID = 0x921
    WMI_RS_CFG_DONE_EVENTID = 0x1921

    @Pyro4.expose
    def wmi_rs_cfg(self, cid, rs_enable=True, **kwargs):
        '''Rate search parameters configuration per connection */

        struct wmi_rs_cfg_cmd {
            /* connection id */
            u8 cid;
            /* enable or disable rate search */
            u8 rs_enable;
            /* rate search configuration */
            struct wmi_rs_cfg rs_cfg;
        } __packed;

        struct wmi_rs_cfg {
            /* The maximal allowed PER for each MCS
             * MCS will be considered as failed if PER during RS is higher
             */
            u8 per_threshold[WMI_NUM_MCS];
            /* Number of MPDUs for each MCS
             * this is the minimal statistic required to make an educated
             * decision
             */
            u8 min_frame_cnt[WMI_NUM_MCS];
            /* stop threshold [0-100] */
            u8 stop_th;
            /* MCS1 stop threshold [0-100] */
            u8 mcs1_fail_th;
            u8 max_back_failure_th;
            /* Debug feature for disabling internal RS trigger (which is
             * currently triggered by BF Done)
             */
            u8 dbg_disable_internal_trigger;
            __le32 back_failure_mask;
            __le32 mcs_en_vec;
        } __packed;

        struct wmi_rs_cfg_done_event {
            u8 cid;
            /* enum wmi_fw_status */
            u8 status;
            u8 reserved[2];
        } __packed;
        '''
        rs_enable = 0x01 if rs_enable else 0x00
        per_threshold = kwargs.get(
            'per_threshold',
            [00, 00, 40, 15, 10, 00, 20, 15, 10, 00, 15, 10, 10])
        min_frame_cnt = kwargs.get(
            'min_frame_cnt',
            [0x00, 0x20, 0x40, 0x40, 0x40, 0x00, 0x50, 0x50, 0x50, 0x00, 0xA0,
             0xA0, 0xA0])
        stop_th = kwargs.get('stop_th', 0x01)
        mcs1_fail_th = kwargs.get('mcs1_fail_th', 0x50)
        max_back_failure_th = kwargs.get('max_back_failure_th', 0x03)
        dbg_disable_internal_trigger = kwargs.get(
            'dbg_disable_internal_trigger', 0x00)
        back_failure_mask = kwargs.get('back_failure_mask', 0x0010)
        mcs_en_vec = kwargs.get('mcs_en_vec', 0x1dde)

        wmi_rs_cfg_data = struct.pack(
            'BB BBBBBBBBBBBBB BBBBBBBBBBBBB BBBB II',
            cid, rs_enable, *per_threshold, *min_frame_cnt, stop_th,
            mcs1_fail_th, max_back_failure_th, dbg_disable_internal_trigger,
            back_failure_mask, mcs_en_vec)
        evt = self.call_wmi(self.WMI_RS_CFG_CMDID, wmi_rs_cfg_data)[0]
        if evt['id'] == self.WMI_RS_CFG_DONE_EVENTID:
            r = struct.unpack('BBxx', evt['data'])
            if r[0] == cid and r[1] == 0x00:
                return {
                    'rs_enable': rs_enable, 'per_threshold': per_threshold,
                    'min_frame_cnt': min_frame_cnt, 'stop_th': stop_th,
                    'mcs1_fail_th': mcs1_fail_th, 'max_back_failure_th':
                    max_back_failure_th, 'dbg_disable_internal_trigger':
                    dbg_disable_internal_trigger, 'back_failure_mask':
                    back_failure_mask, 'mcs_en_vec': mcs_en_vec}
        return None

    WMI_GET_DETAILED_RS_RES_CMDID = 0x922
    WMI_GET_DETAILED_RS_RES_EVENTID = 0x1922

    @Pyro4.expose
    def wmi_get_detailed_rs_res(self, cid):
        payload = struct.pack('B x x x', cid)
        evt = self.call_wmi(self.WMI_GET_DETAILED_RS_RES_CMDID, payload)[0]
        if evt['id'] == self.WMI_GET_DETAILED_RS_RES_EVENTID:
            r = struct.unpack('BB BBBBBBBBBBBBB BBBBBBBBBBBBB <I B xxx',
                              evt['data'])
            rs_res = {'cid': r[0], 'status': r[1], 'num_of_tx_pkt': r[2:15],
                      'num_of_non_acked_pkt': r[15:28], 'tsf': r[28],
                      'mcs': r[29]}
            return rs_res
        return None

    WMI_BF_CONTROL_CMDID = 0x9AA
    WMI_BF_CONTROL_EVENTID = 0x19AA

    @Pyro4.expose
    def wmi_bf_control(self, cid, **kwargs):
        '''
        enum wmi_bf_triggers {
           WMI_BF_TRIGGER_RS_MCS1_TH_FAILURE            = 0x01,
           WMI_BF_TRIGGER_RS_MCS1_NO_BACK_FAILURE       = 0x02,
           WMI_BF_TRIGGER_MAX_CTS_FAILURE_IN_TXOP       = 0x04,
           WMI_BF_TRIGGER_MAX_BACK_FAILURE              = 0x08,
           WMI_BF_TRIGGER_FW                            = 0x10,
           WMI_BF_TRIGGER_MAX_CTS_FAILURE_IN_KEEP_ALIVE = 0x20,
           WMI_BF_TRIGGER_AOA                           = 0x40,
           WMI_BF_TRIGGER_MAX_CTS_FAILURE_IN_UPM        = 0x80,
        };

        struct wmi_bf_control_cmd {
           /* wmi_bf_triggers */
           __le32 triggers;
           u8 cid;
           /* DISABLED = 0, ENABLED = 1 , DRY_RUN = 2 */
           u8 txss_mode;
           /* DISABLED = 0, ENABLED = 1, DRY_RUN = 2 */
           u8 brp_mode;
           /* Max cts threshold (correspond to
            * WMI_BF_TRIGGER_MAX_CTS_FAILURE_IN_TXOP)
            */
           u8 bf_trigger_max_cts_failure_thr;
           /* Max cts threshold in dense (correspond to
            * WMI_BF_TRIGGER_MAX_CTS_FAILURE_IN_TXOP)
            */
           u8 bf_trigger_max_cts_failure_dense_thr;
           /* Max b-ack threshold (correspond to
            * WMI_BF_TRIGGER_MAX_BACK_FAILURE)
            */
           u8 bf_trigger_max_back_failure_thr;
           /* Max b-ack threshold in dense (correspond to
            * WMI_BF_TRIGGER_MAX_BACK_FAILURE)
            */
           u8 bf_trigger_max_back_failure_dense_thr;
           u8 reserved0;
           /* Wrong sectors threshold */
           __le32 wrong_sector_bis_thr;
           /* BOOL to enable/disable long term trigger */
           u8 long_term_enable;
           /* 1 = Update long term thresholds from the long_term_mbps_th_tbl
            * and long_term_trig_timeout_per_mcs arrays, 0 = Ignore
            */
           u8 long_term_update_thr;
           /* Long term throughput threshold [Mbps] */
           u8 long_term_mbps_th_tbl[WMI_NUM_MCS];
           u8 reserved1;
           /* Long term timeout threshold table [msec] */
           __le16 long_term_trig_timeout_per_mcs[WMI_NUM_MCS];
           u8 reserved2[2];
        } __packed;

        struct wmi_bf_control_event {
           /* wmi_fw_status */
           u8 status;
           u8 reserved[3];
        } __packed;
        '''
        bf_trigger_rs_mcs1_th_failure = kwargs.get(
            'bf_trigger_rs_mcs1_th_failure', False) * 0x01
        bf_trigger_rs_mcs1_no_back_failure = kwargs.get(
            'bf_trigger_rs_mcs1_no_back_failure', False) * 0x02
        bf_trigger_max_cts_failure_in_txop = kwargs.get(
            'bf_trigger_max_cts_failure_in_txop', False) * 0x04
        bf_trigger_max_back_failure = kwargs.get(
            'bf_trigger_max_back_failure', False) * 0x08
        bf_trigger_fw = kwargs.get(
            'bf_trigger_fw', False) * 0x10
        bf_trigger_max_cts_failure_in_keep_alive = kwargs.get(
            'bf_trigger_max_cts_failure_in_keep_alive', False) * 0x20
        bf_trigger_aoa = kwargs.get(
            'bf_trigger_aoa', False) * 0x40
        bf_trigger_max_cts_failure_in_upm = kwargs.get(
            'bf_trigger_max_cts_failure_in_upm', False) * 0x80

        bf_triggers = bf_trigger_rs_mcs1_th_failure +\
            bf_trigger_rs_mcs1_no_back_failure +\
            bf_trigger_max_cts_failure_in_txop +\
            bf_trigger_max_back_failure +\
            bf_trigger_fw +\
            bf_trigger_max_cts_failure_in_keep_alive +\
            bf_trigger_aoa +\
            bf_trigger_max_cts_failure_in_upm

        txss_mode = kwargs.get('txss_mode', 0x00)
        brp_mode = kwargs.get('brp_mode', 0x00)
        bf_trigger_max_cts_failure_thr = kwargs.get(
            'bf_trigger_max_cts_failure_thr', 0x00)
        bf_trigger_max_cts_failure_dense_thr = kwargs.get(
            'bf_trigger_max_cts_failure_dense_thr', 0x00)
        bf_trigger_max_back_failure_thr = kwargs.get(
            'bf_trigger_max_back_failure_thr', 0x00)
        bf_trigger_max_back_failure_dense_thr = kwargs.get(
            'bf_trigger_max_back_failure_dense_thr', 0x00)
        wrong_sector_bis_thr = kwargs.get(
            'wrong_sector_bis_thr', 0x00)
        long_term_enable = kwargs.get(
            'long_term_enable', 0x00)
        long_term_update_thr = kwargs.get(
            'long_term_update_thr', 0x00)
        long_term_mbps_th_tbl = kwargs.get(
            'long_term_mbps_th_tbl', [0x00] * 13)
        long_term_trig_timeout_per_mcs = kwargs.get(
            'long_term_trig_timeout_per_mcs', [0x00] * 13)

        payload = struct.pack(
            'I BBBB BBBx I BB BBBBBBBBBBBBB x HHHHHHHHHHHHH xx',
            bf_triggers, cid, txss_mode, brp_mode,
            bf_trigger_max_cts_failure_thr,
            bf_trigger_max_cts_failure_dense_thr,
            bf_trigger_max_back_failure_thr,
            bf_trigger_max_back_failure_dense_thr,
            wrong_sector_bis_thr,
            long_term_enable, long_term_update_thr,
            *long_term_mbps_th_tbl,
            *long_term_trig_timeout_per_mcs)

        evt = self.call_wmi(self.WMI_BF_CONTROL_CMDID, payload)[0]
        if evt['id'] == self.WMI_BF_CONTROL_EVENTID:
            status = struct.unpack('Bxxx', evt['data'])[0]
            if status == 0x00:
                self.logger.info('WMI_FW_STATUS_SUCCESS')
                return {
                    'bf_triggers': bf_triggers, 'cid': cid,
                    'txss_mode': txss_mode, 'brp_mode': brp_mode,
                    'bf_trigger_max_cts_failure_thr':
                    bf_trigger_max_cts_failure_thr,
                    'bf_trigger_max_cts_failure_dense_thr':
                    bf_trigger_max_cts_failure_dense_thr,
                    'bf_trigger_max_back_failure_thr':
                    bf_trigger_max_back_failure_thr,
                    'bf_trigger_max_back_failure_dense_thr':
                    bf_trigger_max_back_failure_dense_thr,
                    'wrong_sector_bis_thr': wrong_sector_bis_thr,
                    'long_term_enable': long_term_enable,
                    'long_term_update_thr': long_term_update_thr,
                    'long_term_mbps_th_tbl': long_term_mbps_th_tbl,
                    'long_term_trig_timeout_per_mcs':
                    long_term_trig_timeout_per_mcs}
            else:
                self.logger.error('WMI_FW_STATUS_FAILURE')
                return None

    WMI_SET_RF_SECTOR_ON_CMDID = 0x9A4
    WMI_SET_RF_SECTOR_ON_DONE_EVENTID = 0x19A4

    @Pyro4.expose
    def wmi_set_rf_sector_on(self, sector, sector_type, rf_modules_vec):
        '''Activates specified sector for specified rf modules

        struct wmi_set_rf_sector_on_cmd {
            /* Sector index to be activated */
            __le16 sector_idx;
            /* type of requested RF sector (enum wmi_rf_sector_type) */
            u8 sector_type;
            /* bitmask vector specifying destination RF modules */
            u8 rf_modules_vec;
        } __packed;

        struct wmi_set_rf_sector_on_done_event {
            /* result status of WMI_SET_RF_SECTOR_ON_CMD (enum
             * wmi_rf_sector_status)
             */
            u8 status;
            /* align to U32 boundary */
            u8 reserved[3];
        } __packed;
        '''
        payload = struct.pack('HBB', sector, sector_type, rf_modules_vec)
        evt = self.call_wmi(self.WMI_SET_RF_SECTOR_ON_CMDID, payload)[0]
        self.logger.info('Setting RF sector on using wmi command')
        if evt['id'] == self.WMI_SET_RF_SECTOR_ON_DONE_EVENTID:
            r = struct.unpack('Bxxx', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_RF_SECTOR_STATUS_SUCCESS')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BAD_PARAMETERS_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BUSY_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_NOT_SUPPORTED_ERROR')
            return r
        return None

    @Pyro4.expose
    def wmi_prio_tx_sectors_order(self, prio, swptype, cid):
        """Set the order of TX sectors in TXSS and/or Beacon(AP).

        WMI_PRIO_TX_SECTORS_ORDER_CMDID         = 0x9A5,
        WMI_PRIO_TX_SECTORS_ORDER_EVENTID       = 0x19A5,

        MAX_NUM_OF_SECTORS  (128)

        struct wmi_prio_tx_sectors_order_cmd {
            /* tx sectors order to be applied, 0xFF for end of array */
            u8 tx_sectors_priority_array[MAX_NUM_OF_SECTORS];
            /* enum wmi_sector_sweep_type, TXSS and/or Beacon */
            u8 sector_sweep_type;
            /* needed only for TXSS configuration */
            u8 cid;
            /* alignment to 32b */
            u8 reserved[2];
        } __packed;

        enum wmi_sector_sweep_type {
            WMI_SECTOR_SWEEP_TYPE_TXSS          = 0x00,
            WMI_SECTOR_SWEEP_TYPE_BCON          = 0x01,
            WMI_SECTOR_SWEEP_TYPE_TXSS_AND_BCON = 0x02,
            WMI_SECTOR_SWEEP_TYPE_NUM           = 0x03,
        };

        /* completion status codes */
        enum wmi_prio_tx_sectors_cmd_status {
            WMI_PRIO_TX_SECT_CMD_STATUS_SUCCESS = 0x00,
            WMI_PRIO_TX_SECT_CMD_STATUS_BAD_PARAM   = 0x01,
            /* other error */
            WMI_PRIO_TX_SECT_CMD_STATUS_ERROR   = 0x02,
        };

        /* WMI_PRIO_TX_SECTORS_ORDER_EVENTID */
        struct wmi_prio_tx_sectors_order_event {
            /* enum wmi_prio_tx_sectors_cmd_status */
            u8 status;
            /* alignment to 32b */
            u8 reserved[3];
        } __packed;

        """
        max_sectors = 128
        payload = struct.pack('B' * max_sectors + 'BBxx', *prio, swptype, cid)
        evt = self.call_wmi(0x9a5, payload)[0]
        self.logger.info('Setting TX sector prio using wmi command')
        if evt['id'] == 0x19a5:
            r = struct.unpack('Bxxx', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_RF_SECTOR_STATUS_SUCCESS')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BAD_PARAMETERS_ERROR')
            elif r == 2:
                self.logger.error('WMI_RF_SECTOR_STATUS_BUSY_ERROR')
            elif r == 3:
                self.logger.error('WMI_RF_SECTOR_STATUS_NOT_SUPPORTED_ERROR')
            return r
        return None

    @Pyro4.expose
    def wmi_prio_tx_sectors_number(self, beacon_num, txss_num, cid):
        """Set the number of active sectors in TXSS and/or Beacon.

        WMI_PRIO_TX_SECTORS_NUMBER_CMDID        = 0x9A6,
        WMI_PRIO_TX_SECTORS_NUMBER_EVENTID      = 0x19A6,

        struct wmi_prio_tx_sectors_number_cmd {
            struct wmi_prio_tx_sectors_num_cmd active_sectors_num;
            /* alignment to 32b */
            u8 reserved;
        } __packed;

        struct wmi_prio_tx_sectors_num_cmd {
            /* [0-128], 0 = No changes */
            u8 beacon_number_of_sectors;
            /* [0-128], 0 = No changes */
            u8 txss_number_of_sectors;
            /* [0-8] needed only for TXSS configuration */
            u8 cid;
        } __packed;

        /* WMI_PRIO_TX_SECTORS_NUMBER_EVENTID */
        struct wmi_prio_tx_sectors_number_event {
            /* enum wmi_prio_tx_sectors_cmd_status */
            u8 status;
            /* alignment to 32b */
            u8 reserved[3];
        } __packed;
        """
        payload = struct.pack('BBBx', beacon_num, txss_num, cid)
        evt = self.call_wmi(0x9a6, payload)[0]
        self.logger.info('Setting TX sector number using wmi command')
        if evt['id'] == 0x19a6 or evt['id'] == 0x19a5:
            r = struct.unpack('Bxxx', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_RF_SECTOR_STATUS_SUCCESS')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BAD_PARAMETERS_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BUSY_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_NOT_SUPPORTED_ERROR')
            return r
        return None

    @Pyro4.expose
    def wmi_ps_dev_profile_cfg(self, ps_profile):
        """ Power save profile to be used by the device

        # WMI_PS_DEV_PROFILE_CFG_CMDID = 0x91C,
        WMI_PS_DEV_PROFILE_CFG_EVENTID = 0x191C,

        /* WMI_PS_DEV_PROFILE_CFG_CMDID
         *
         * Power save profile to be used by the device
         *
         * Returned event:
         * - WMI_PS_DEV_PROFILE_CFG_EVENTID
         */
        struct wmi_ps_dev_profile_cfg_cmd {
            /* wmi_ps_profile_type_e */
            u8 ps_profile;
            u8 reserved[3];
        } __packed;

        /* WMI_PS_DEV_PROFILE_CFG_EVENTID */
        struct wmi_ps_dev_profile_cfg_event {
            /* wmi_ps_cfg_cmd_status_e */
            __le32 status;
        } __packed;

        /* Power Save command completion status codes */
        enum wmi_ps_cfg_cmd_status {
            WMI_PS_CFG_CMD_STATUS_SUCCESS   = 0x00,
            WMI_PS_CFG_CMD_STATUS_BAD_PARAM = 0x01,
            /* other error */
            WMI_PS_CFG_CMD_STATUS_ERROR = 0x02,
        };
        """
        payload = struct.pack('Bxxx', ps_profile)
        evt = self.call_wmi(0x91C, payload)[0]
        self.logger.info('Setting Power save profile using wmi command')
        if evt['id'] == 0x191C:
            r = struct.unpack('I', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_PS_CFG_CMD_STATUS_SUCCESS')
            elif r == 1:
                self.logger.error('WMI_PS_CFG_CMD_STATUS_BAD_PARAM')
            elif r == 2:
                self.logger.error('WMI_PS_CFG_CMD_STATUS_ERROR')
            return r
        return None

    @Pyro4.expose
    def wmi_ps_dev_profile_cfg_read(self):
        """ Read the current power profile
        WMI_PS_DEV_PROFILE_CFG_READ_CMDID = 0x942
        WMI_PS_DEV_PROFILE_CFG_READ_EVENTID = 0x1942

        /* Device Power Save Profiles */
        enum wmi_ps_profile_type {
            WMI_PS_PROFILE_TYPE_DEFAULT     = 0x00,
            WMI_PS_PROFILE_TYPE_PS_DISABLED     = 0x01,
            WMI_PS_PROFILE_TYPE_MAX_PS      = 0x02,
            WMI_PS_PROFILE_TYPE_LOW_LATENCY_PS  = 0x03,
        };

        /* WMI_PS_DEV_PROFILE_CFG_READ_CMDID */
        struct wmi_ps_dev_profile_cfg_read_cmd {
            /* reserved */
            __le32 reserved;
        } __packed;

        /* WMI_PS_DEV_PROFILE_CFG_READ_EVENTID */
        struct wmi_ps_dev_profile_cfg_read_event {
            /* wmi_ps_profile_type_e */
            u8 ps_profile;
            u8 reserved[3];
        } __packed;
        """

        payload = bytearray(4)
        evt = self.call_wmi(0x942, payload)[0]
        self.logger.info('Reading current power profile')
        if evt['id'] == 0x1942:
            r = struct.unpack('Bxxx', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_PS_PROFILE_TYPE_DEFAULT')
            elif r == 1:
                self.logger.info('WMI_PS_PROFILE_TYPE_PS_DISABLED')
            elif r == 2:
                self.logger.info('WMI_PS_PROFILE_TYPE_MAX_PS')
            elif r == 3:
                self.logger.info('WMI_PS_PROFILE_TYPE_LOW_LATENCY_PS')
            return r
        return None

    @Pyro4.expose
    def wmi_prio_tx_sectors_default_cfg(self, swptype, cid):
        '''Set default sectors order and number (hard coded in board file)
        in TXSS and/or Beacon.

        WMI_PRIO_TX_SECTORS_SET_DEFAULT_CFG_CMDID = 0x9A7,
        WMI_PRIO_TX_SECTORS_SET_DEFAULT_CFG_EVENTID = 0x19A7,

        struct wmi_prio_tx_sectors_set_default_cfg_cmd {
            /* enum wmi_sector_sweep_type, TXSS and/or Beacon */
            u8 sector_sweep_type;
            /* needed only for TXSS configuration */
            u8 cid;
            /* alignment to 32b */
            u8 reserved[2];
        } __packed;

        /* WMI_PRIO_TX_SECTORS_SET_DEFAULT_CFG_EVENTID */
        struct wmi_prio_tx_sectors_set_default_cfg_event {
            /* enum wmi_prio_tx_sectors_cmd_status */
            u8 status;
            /* alignment to 32b */
            u8 reserved[3];
        } __packed;
        '''
        payload = struct.pack('BBxx', swptype, cid)
        evt = self.call_wmi(0x9a7, payload)[0]
        self.logger.info('Setting TX sector number using wmi command')
        if evt['id'] == 0x19a7 or evt['id'] == 0x19a5:
            r = struct.unpack('Bxxx', evt['data'])[0]
            if r == 0:
                self.logger.info('WMI_RF_SECTOR_STATUS_SUCCESS')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BAD_PARAMETERS_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_BUSY_ERROR')
            elif r == 1:
                self.logger.error('WMI_RF_SECTOR_STATUS_NOT_SUPPORTED_ERROR')
            return r
        return None

    @Pyro4.expose
    def wmi_aoa_meas(self, peer, channel, meas_type, rf_mask):
        '''
        WMI_AOA_MEAS_CMDID = 0x923,
        WMI_AOA_MEAS_EVENTID = 0x1923,

        WMI_AOA_MAX_DATA_SIZE   (128)

        enum wmi_aoa_meas_type {
            WMI_AOA_PHASE_MEAS  = 0x00,
            WMI_AOA_PHASE_AMP_MEAS  = 0x01,
        };

        /* WMI_AOA_MEAS_CMDID */
        struct wmi_aoa_meas_cmd {
            u8 mac_addr[WMI_MAC_LEN];
            /* channels IDs:
             * 0 - 58320 MHz
             * 1 - 60480 MHz
             * 2 - 62640 MHz
             */
            u8 channel;
            /* enum wmi_aoa_meas_type */
            u8 aoa_meas_type;
            __le32 meas_rf_mask;
        } __packed;

        enum wmi_aoa_meas_status {
            WMI_AOA_MEAS_SUCCESS        = 0x00,
            WMI_AOA_MEAS_PEER_INCAPABLE = 0x01,
            WMI_AOA_MEAS_FAILURE        = 0x02,
        };

        /* WMI_AOA_MEAS_EVENTID */
        struct wmi_aoa_meas_event {
            u8 mac_addr[WMI_MAC_LEN];
            /* channels IDs:
             * 0 - 58320 MHz
             * 1 - 60480 MHz
             * 2 - 62640 MHz
             */
            u8 channel;
            /* enum wmi_aoa_meas_type */
            u8 aoa_meas_type;
            /* Measurments are from RFs, defined by the mask */
            __le32 meas_rf_mask;
            /* enum wmi_aoa_meas_status */
            u8 meas_status;
            u8 reserved;
            /* Length of meas_data in bytes */
            __le16 length;
            u8 meas_data[WMI_AOA_MAX_DATA_SIZE];
        } __packed;
    '''
        print('Obtaining AoA Information')
        addr = [b for b in mac_addr_to_bytearray(peer)]
        payload = struct.pack('BBBBBB BB I', *addr, channel, meas_type,
                              rf_mask)
        evts = self.call_wmi(0x923, payload)
        evt = [e for e in evts if e['id'] == 0x1923]
        if evt:
            evt = evt[0]
        else:
            return None
        header = struct.unpack_from('BBBBBB BB I Bx H', evt['data'])
        if header[9] == 0x00:
            print('WMI_AOA_MEAS_SUCCESS')
            self.logger.info('WMI_AOA_MEAS_SUCCESS')
            data_length = header[-1]
            self.logger.info('Extracted %d bytes' % data_length)
            meas_data = struct.unpack_from('H' * round(data_length / 2), evt['data'][16:])
            print(meas_data)
            return meas_data
        elif header[9] == 0x01:
            self.logger.error('WMI_AOA_MEAS_PEER_INCAPABLE')

            return None
        elif header[9] == 0x02:
            self.logger.error('WMI_AOA_MEAS_FAILURE')
            return None

    WMI_SET_ACTIVE_SILENT_RSSI_TABLE_CMDID = 0x85C
    WMI_SET_SILENT_RSSI_TABLE_DONE_EVENTID = 0x185C

    RF_TEMPERATURE_CALIB_DEFAULT_DB = 0x00
    RF_TEMPERATURE_CALIB_HIGH_POWER_DB = 0x01

    @Pyro4.expose
    def wmi_silent_rssi_table(self, wmi_silent_rssi_table):
        '''
        /* WMI_SILENT_RSSI_TABLE */
        enum wmi_silent_rssi_table {
            RF_TEMPERATURE_CALIB_DEFAULT_DB     = 0x00,
            RF_TEMPERATURE_CALIB_HIGH_POWER_DB  = 0x01,
        };

        /* WMI_SILENT_RSSI_STATUS */
        enum wmi_silent_rssi_status {
            SILENT_RSSI_SUCCESS = 0x00,
            SILENT_RSSI_FAILURE = 0x01,
        };

        /* WMI_SET_ACTIVE_SILENT_RSSI_TABLE_CMDID */
        struct wmi_set_active_silent_rssi_table_cmd {
            /* enum wmi_silent_rssi_table */
            __le32 table;
        } __packed;

        /* WMI_SET_SILENT_RSSI_TABLE_DONE_EVENTID */
        struct wmi_set_silent_rssi_table_done_event {
            /* enum wmi_silent_rssi_status */
            __le32 status;
            /* enum wmi_silent_rssi_table */
            __le32 table;
        } __packed;
    '''
        payload = struct.pack('I', wmi_silent_rssi_table)
        cmd_id = self.WMI_SET_ACTIVE_SILENT_RSSI_TABLE_CMDID
        evt = self.call_wmi(cmd_id, payload)[0]
        if evt['id'] == self.WMI_SET_SILENT_RSSI_TABLE_DONE_EVENTID:
            r = struct.unpack('II', evt['data'])
            wmi_silent_rssi_status = r[0]
            wmi_silent_rssi_table = r[1]

            if wmi_silent_rssi_status == 0:
                return wmi_silent_rssi_table
            else:
                self.logger.error('SILENT_RSSI_FAILURE')
        return None



        # Thermal Throttling is disabled by default
    # WMI_GET_THERMAL_THROTTLING_CFG_CMDID = 0x941
    # WMI_GET_THERMAL_THROTTLING_CFG_EVENTID = 0x1941

    # @Pyro4.expose
    # def wmi_get_thermal_throttling_cfg(self):
    #     '''
    #     /* WMI_GET_THERMAL_THROTTLING_CFG_EVENTID */
    #     struct wmi_get_thermal_throttling_cfg_event {
    #         /* Status data */
    #         struct wmi_tt_data tt_data;
    #     } __packed;

    #     /* Zones: HIGH, MAX, CRITICAL */
    #     #define WMI_NUM_OF_TT_ZONES (3)

    #     struct wmi_tt_zone_limits {
    #         /* Above this temperature this zone is active */
    #         u8 temperature_high;
    #         /* Below this temperature the adjacent lower zone is active */
    #         u8 temperature_low;
    #         u8 reserved[2];
    #     } __packed;

    #     /* Struct used for both configuration and status commands of thermal
    #      * throttling
    #      */
    #     struct wmi_tt_data {
    #         /* Enable/Disable TT algorithm for baseband */
    #         u8 bb_enabled;
    #         u8 reserved0[3];
    #         /* Define zones for baseband */
    #         struct wmi_tt_zone_limits bb_zones[WMI_NUM_OF_TT_ZONES];
    #         /* Enable/Disable TT algorithm for radio */
    #         u8 rf_enabled;
    #         u8 reserved1[3];
    #         /* Define zones for all radio chips */
    #         struct wmi_tt_zone_limits rf_zones[WMI_NUM_OF_TT_ZONES];
    #     } __packed;

    #     /* WMI_SET_THERMAL_THROTTLING_CFG_CMDID */
    #     struct wmi_set_thermal_throttling_cfg_cmd {
    #         /* Command data */
    #         struct wmi_tt_data tt_data;
    #     } __packed;
    #     '''
    #     payload = bytearray(4)
    #     cmd_id = self.WMI_GET_THERMAL_THROTTLING_CFG_CMDID
    #     evt = self.call_wmi(cmd_id, payload)[0]
    #     if evt['id'] == self.WMI_GET_THERMAL_THROTTLING_CFG_EVENTID:
    #         return evt['data'].hex()
    #         # r = struct.unpack_from('Bxxx BBxx BBxx BBxx Bxxx BBxx BBxx BBxx Bxxx', evt['data'])
    #         # return {
    #         #     'bb_enabled': r[0],
    #         #     'bb_high': [r[1], r[3], r[5]],
    #         #     'bb_low': [r[2], r[4], r[6]],
    #         #     'rf_enabled': r[7],
    #         #     'rf_high': [r[8], r[10], r[12]],
    #         #     'rf_low': [r[9], r[11], r[13]]}
    #     return None
