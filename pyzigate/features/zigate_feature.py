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
            msg = self.decode_struct(struct, msg_data)

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
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8001 : Log Message')
            ZGT_LOG.debug('  - Log Level : {}'.format(zgt_log_levels[msg['level']]))
            ZGT_LOG.debug('  - Log Info  : {}'.format(msg['info']))

            return True

        # Default Response
        elif msg_type == b'8101':
            struct = OrderedDict([('sequence', 8), ('endpoint', 8),
                                  ('cluster', 16), ('command_id', 8),
                                  ('status', 8)])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8101 : Default Response')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - EndPoint       : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Cluster id     : {} ({})'.format(
                msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            ZGT_LOG.debug('  - Command        : {}'.format(msg['command_id']))
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))

            return True

        # Version List
        if msg_type == b'8010':
            struct = OrderedDict([('major', 'int16'), ('installer', 'int16')])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE : Version List')
            ZGT_LOG.debug('  - Major version     : {}'.format(msg['major']))
            ZGT_LOG.debug('  - Installer version : {}'.format(msg['installer']))

            return True

        # APS Data Confirm Fail
        if msg_type == b'8702':
            struct = OrderedDict([('status', 8), ('src_endpoint', 8),
                                  ('dst_endpoint', 8), ('dst_address_mode', 8),
                                  ('dst_address', 64), ('sequence', 8)])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8702 : APS Data Confirm Fail')
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))
            ZGT_LOG.debug('  - Src endpoint   : {}'.format(msg['src_endpoint']))
            ZGT_LOG.debug('  - Dst endpoint   : {}'.format(msg['dst_endpoint']))
            ZGT_LOG.debug('  - Dst mode       : {}'.format(msg['dst_address_mode']))
            ZGT_LOG.debug('  - Dst address    : {}'.format(msg['dst_address']))
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))

            return True

        # TODO 0x8009
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

# Zigate -> Obj	0x0020	Set Expended PANID	<64-bit Extended PAN ID:uint64_t>
# Zigate -> Obj	0x0021	Set Channel Mask	<channel mask:uint32_t>
# Zigate -> Obj	0x0022	Set Security State + Key	<key type: uint8_t>
# <key: data>
# Zigate -> Obj	0x0023	Set device Type	<device type: uint8_t>
# Device Types:
# 0 = Coordinator
# 1 = Router
# 2 = Legacy Router
# Zigate -> Obj	0x0024	Start Network
# ==> Network Joined / Formed
# Zigate -> Obj	0x0025	Start Network Scan
# ==> Network Joined / Formed
# Zigate -> Obj	0x0027	Enable Permissions Controlled Joins	<Enable/Disable : uint8_t>	Status
# 1 – Enable
# 2 – Disable
