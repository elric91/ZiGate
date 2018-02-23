import logging
from binascii import hexlify
from collections import OrderedDict

from .abstract_feature import AbstractFeature, CLUSTERS

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0000'

    def get_name(self):
        return 'Zigate buitin'

    def decode_msg(self, zigate, msg_type, msg_data):
        # Status
        if msg_type == b'8000':
            struct = OrderedDict([('status', 'int'), ('sequence', 8),
                                  ('packet_type', 16), ('info', 'rawend')])
            msg = zigate.decode_struct(struct, msg_data)

            status_codes = {0: 'Success', 1: 'Invalid parameters',
                            2: 'Unhandled command', 3: 'Command failed',
                            4: 'Busy', 5: 'Stack already started'}
            status_text = status_codes.get(msg['status'],
                                           'Failed with event code: %i' %
                                           msg['status'])

            ZGT_LOG.debug('RESPONSE 8000 : Status')
            ZGT_LOG.debug('  * Status              : {}'.format(status_text))
            ZGT_LOG.debug('  - Sequence            : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Response to command : {}'.format(msg['packet_type']))
            if hexlify(msg['info']) != b'00':
                ZGT_LOG.debug('  - Additional msg: ', msg['info'])

            return True

        # Log Response
        if msg_type == b'8001':
            zgt_log_levels = ['Emergency', 'Alert', 'Critical', 'Error',
                              'Warning', 'Notice', 'Information', 'Debug']
            struct = OrderedDict([('level', 'int'), ('info', 'rawend')])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8001 : Log Message')
            ZGT_LOG.debug('  - Log Level : {}'.format(zgt_log_levels[msg['level']]))
            ZGT_LOG.debug('  - Log Info  : {}'.format(msg['info']))

            return True

        # Network State response
        if msg_type == b'8009':
            struct = OrderedDict([('short_addr', 16),
                                  ('ext_addr', 64),
                                  ('pan_id', 16),
                                  ('extpan_id', 64),
                                  ('channel', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE : Network State response')
            ZGT_LOG.debug('  - Short Address    : {}'.format(msg['short_addr']))
            ZGT_LOG.debug('  - Extended Address : {}'.format(msg['ext_addr']))
            ZGT_LOG.debug('  - PAN ID           : {}'.format(msg['pan_id']))
            ZGT_LOG.debug('  - Extended PAN ID  : {}'.format(msg['extpan_id']))
            ZGT_LOG.debug('  - Channel          : {}'.format(msg['channel']))
            return True

        # Version List
        if msg_type == b'8010':
            struct = OrderedDict([('major', 'int16'), ('installer', 'int16')])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE : Version List')
            ZGT_LOG.debug('  - Major version     : {}'.format(msg['major']))
            ZGT_LOG.debug('  - Installer version : {}'.format(msg['installer']))

            return True

        # Network joined / formed
        if msg_type == b'8024':
            struct = OrderedDict([('status', 8), ('short_addr', 16), ('extended_addr', 64), ('channel', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            status = 'Unknown'
            if msg['status'] == b'00':
                status = 'Joined existing network'
            elif msg['status'] == b'01':
                status = 'Formed new network'
            elif b'80' <= msg['status'] <= b'F4':
                status = 'Failed (ZigBee event codes)'

            ZGT_LOG.debug('RESPONSE : Network joined / formed')
            ZGT_LOG.debug('  - Status            : {}'.format(status))
            ZGT_LOG.debug('  - Short Address     : {}'.format(msg['short_addr']))
            ZGT_LOG.debug('  - Extended Address  : {}'.format(msg['extended_addr']))
            ZGT_LOG.debug('  - Channel           : {}'.format(msg['channel']))
            return True

        # Default Response
        if msg_type == b'8101':
            struct = OrderedDict([('sequence', 8), ('endpoint', 8),
                                  ('cluster', 16), ('command_id', 8),
                                  ('status', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8101 : Default Response')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - EndPoint       : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Cluster id     : {} ({})'.format(
                msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            ZGT_LOG.debug('  - Command        : {}'.format(msg['command_id']))
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))

            return True

        # APS Data Confirm Fail
        if msg_type == b'8702':
            struct = OrderedDict([('status', 8), ('src_endpoint', 8),
                                  ('dst_endpoint', 8), ('dst_address_mode', 8),
                                  ('dst_address', 64), ('sequence', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8702 : APS Data Confirm Fail')
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))
            ZGT_LOG.debug('  - Src endpoint   : {}'.format(msg['src_endpoint']))
            ZGT_LOG.debug('  - Dst endpoint   : {}'.format(msg['dst_endpoint']))
            ZGT_LOG.debug('  - Dst mode       : {}'.format(msg['dst_address_mode']))
            ZGT_LOG.debug('  - Dst address    : {}'.format(msg['dst_address']))
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))

            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Zigate command sending.
    """

    def network_state(self):
        """
        Get Network State

        :type self: Zigate
        """
        self.send_data("0009")

    def get_version(self):
        """
        Get Version

        :type self: Zigate
        """
        self.send_data("0010")

    def reset(self):
        """
        Reset

        :type self: Zigate
        """
        self.send_data("0011")

    def erase_persistent_data(self):
        """
        Erase Persistent Data

        :type self: Zigate
        """
        self.send_data("0012")

    def factory_reset(self):
        """
        Erase Persistent Data

        :type self: Zigate
        """
        self.send_data("0013")

    def set_expanded_panid(self, expanded_pan_id):
        """
        Set Expended PANID

        :type self: Zigate
        :type expanded_pan_id: uint64_t
        """
        self.send_data("0020", '{:08x}'.format(expanded_pan_id))

    def set_channel(self, channel_mask):
        """
        Set Channel Mask

        :type self: Zigate
        :type channel_mask: uint32_t
        """
        self.send_data("0021", '{:04x}'.format(channel_mask))

    def set_device_type(self, device_type):
        """
        Set Channel Mask

        :type self: Zigate
        :type device_type: DeviceType
        """
        self.send_data("0021", '{:02x}'.format(device_type))

    def start_network(self, scan=False):
        """
        Start Network

        :type self: Zigate
        :type scan: bool
        """
        self.send_data("0025" if scan else "0024")

    def switch_permission_controlled_join(self, permission_controlled_join=True):
        """
        Start Network

        :type self: Zigate
        :type permission_controlled_join: bool
        """
        self.send_data("0027", '{:02x}'.format(1 if permission_controlled_join else 2))
