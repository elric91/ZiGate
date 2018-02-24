import logging
from collections import OrderedDict

from ..zgt_parameters import *
from .abstract_feature import AbstractFeature, CLUSTERS

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0000'

    def get_name(self):
        return 'Description'

    def decode_msg(self, zigate, msg_type, msg_data):
        # Liste des clusters de l'objet
        if msg_type == b'8003':
            struct = OrderedDict([('endpoint', 8),  ('profile', 16),
                                  ('cluster_count', 'count'), ('cluster_list', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8003 : Liste des clusters de l\'objet')
            ZGT_LOG.debug('  - EndPoint          : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Profile ID        : {}'.format(msg['profile']))
            ZGT_LOG.debug('  - Cluster count     : {}'.format(msg['cluster_count']))
            for i, cluster_id in enumerate(msg['cluster_list']):
                ZGT_LOG.debug('    - Cluster %s : %s (%s)' % (i, cluster_id, CLUSTERS.get(cluster_id, 'unknown')))
            return True

        # Liste des attributs de l'objet
        if msg_type == b'8004':
            struct = OrderedDict([('endpoint', 8),('profile', 16), ('cluster', 16),
                                  ('attr_count', 'count'), ('attr_list', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8004 : Liste des attributs de l\'objet')
            ZGT_LOG.debug('  - EndPoint          : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Profile ID        : {}'.format(msg['profile']))
            ZGT_LOG.debug('  - Cluster           : %s - %s' % (msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            ZGT_LOG.debug('  - Attrs count       : {}'.format(msg['attr_count']))
            for i, attr_id in enumerate(msg['attr_list']):
                ZGT_LOG.debug('    - Attribute %s : %s' % (i, attr_id))
            return True

        # Liste des commandes de l'objet
        if msg_type == b'8005':
            struct = OrderedDict([('endpoint', 8),('profile', 16), ('cluster', 16),
                                  ('cmd_count', 'count'), ('cmd_list', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8005 : Liste des commandes de l\'objet')
            ZGT_LOG.debug('  - EndPoint          : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Profile ID        : {}'.format(msg['profile']))
            ZGT_LOG.debug('  - Cluster           : %s - %s' % (msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            ZGT_LOG.debug('  - Cmd count         : {}'.format(msg['cmd_count']))
            for i, cmd_id in enumerate(msg['cmd_list']):
                ZGT_LOG.debug('    - Attribute %s : %s' % (i, cmd_id))
            return True

        # Network Address
        if msg_type == b'8040':
            struct = OrderedDict([('sequence', 8), ('status', 8),
                                  ('IEEE_addr', 64), ('addr', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8040 : Network Address response')
            ZGT_LOG.debug('  - Sequence          : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status            : {}'.format(msg['status']))
            ZGT_LOG.debug('  - IEEE address      : {}'.format(msg['IEEE_addr']))
            ZGT_LOG.debug('  - From address      : {}'.format(msg['addr']))
            return True

        # IEEE Address
        if msg_type == b'8041':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('IEEE_addr', 64),
                                  ('addr', 16),
                                  ('associated_devices', 8), ('start_idx', 16),
                                  ('device_count', 'count'), ('device_list', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8041 : IEEE Address response')
            ZGT_LOG.debug('  - Sequence          : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status            : {}'.format(msg['status']))
            ZGT_LOG.debug('  - IEEE address      : {}'.format(msg['IEEE_addr']))
            ZGT_LOG.debug('  - From address      : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - Assoc. Devices    : {}'.format(msg['associated_devices']))
            ZGT_LOG.debug('  - Start Index       : {}'.format(msg['start_idx']))
            ZGT_LOG.debug('  - Device Count      : {}'.format(msg['device_count']))
            for i, device_id in enumerate(msg['device_list'], 1):
                ZGT_LOG.debug('    - %s : %s' % (i, device_id))
            return True

        # Node Descriptor
        if msg_type == b'8042':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('manufacturer_code', 16),
                                  ('max_rx', 16), ('max_tx', 16),
                                  ('server_mask', 16),
                                  ('descriptor_capability', 8),
                                  ('mac_flags', 8), ('max_buffer_size', 16),
                                  ('bit_field', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            server_mask_binary = format(int(msg['server_mask'], 16), '016b')
            descriptor_capability_binary = format(int(msg['descriptor_capability'], 16), '08b')
            mac_flags_binary = format(int(msg['mac_flags'], 16), '08b')
            bit_field_binary = format(int(msg['bit_field'], 16), '016b')

            # Length 16, 7-15 Reserved
            server_mask_desc = ['Primary trust center',
                                'Back up trust center',
                                'Primary binding cache',
                                'Backup binding cache',
                                'Primary discovery cache',
                                'Backup discovery cache',
                                'Network manager']
            # Length 8, 2-7 Reserved
            descriptor_capability_desc = ['Extended Active endpoint list',
                                          'Extended simple descriptor list']
            # Length 8
            mac_capability_desc = ['Alternate PAN Coordinator', 'Device Type',
                                   'Power source', 'Receiver On when Idle',
                                   'Reserved', 'Reserved',
                                   'Security capability', 'Allocate Address']
            # Length 16
            bit_field_desc = ['Logical type: Coordinator',
                              'Logical type: Router',
                              'Logical type: End Device',
                              'Complex descriptor available',
                              'User descriptor available', 'Reserved',
                              'Reserved', 'Reserved',
                              'APS Flag', 'APS Flag', 'APS Flag',
                              'Frequency band', 'Frequency band',
                              'Frequency band', 'Frequency band',
                              'Frequency band']

            ZGT_LOG.debug('RESPONSE 8042 : Node Descriptor')
            ZGT_LOG.debug('  - Sequence          : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status            : {}'.format(msg['status']))
            ZGT_LOG.debug('  - From address      : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - Manufacturer code : {}'.format(msg['manufacturer_code']))
            ZGT_LOG.debug('  - Max Rx size       : {}'.format(msg['max_rx']))
            ZGT_LOG.debug('  - Max Tx size       : {}'.format(msg['max_tx']))
            ZGT_LOG.debug('  - Server mask       : {}'.format(msg['server_mask']))
            ZGT_LOG.debug('    - Binary          : {}'.format(server_mask_binary))
            for i, description in enumerate(server_mask_desc, 1):
                ZGT_LOG.debug('    - %s : %s' % (description, 'Yes' if server_mask_binary[-i] == '1' else 'No'))
            ZGT_LOG.debug('  - Descriptor        : {}'.format(msg['descriptor_capability']))
            ZGT_LOG.debug('    - Binary          : {}'.format(descriptor_capability_binary))
            for i, description in enumerate(descriptor_capability_desc, 1):
                ZGT_LOG.debug('    - %s : %s' % (
                    description, 'Yes' if descriptor_capability_binary[-i] == '1' else 'No'))
            ZGT_LOG.debug('  - Mac flags         : {}'.format(msg['mac_flags']))
            ZGT_LOG.debug('    - Binary          : {}'.format(mac_flags_binary))
            for i, description in enumerate(mac_capability_desc, 1):
                ZGT_LOG.debug('    - %s : %s' % (description, 'Yes'if mac_flags_binary[-i] == '1' else 'No'))
            ZGT_LOG.debug('  - Max buffer size   : {}'.format(msg['max_buffer_size']))
            ZGT_LOG.debug('  - Bit field         : {}'.format(msg['bit_field']))
            ZGT_LOG.debug('    - Binary          : {}'.format(bit_field_binary))
            for i, description in enumerate(bit_field_desc, 1):
                ZGT_LOG.debug('    - %s : %s' % (description, 'Yes' if bit_field_binary[-i] == '1' else 'No'))
            return True

        # Simple Descriptor
        if msg_type == b'8043':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('length', 8), ('endpoint', 8),
                                  ('profile', 16), ('device_id', 16),
                                  ('bit', 8), ('in_cluster_count', 'count'),
                                  ('in_cluster_list', 16),
                                  ('out_cluster_count', 'count'),
                                  ('out_cluster_list', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8043 : Cluster List')
            ZGT_LOG.debug('  - Sequence          : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status            : {}'.format(msg['status']))
            ZGT_LOG.debug('  - From address      : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - Length            : {}'.format(msg['length']))
            ZGT_LOG.debug('  - EndPoint          : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Profile ID        : {}'.format(msg['profile']))
            ZGT_LOG.debug('  - Device ID         : {}'.format(msg['device_id']))
            ZGT_LOG.debug('  - IN cluster count  : {}'.format(msg['in_cluster_count']))
            for i, cluster_id in enumerate(msg['in_cluster_list']):
                ZGT_LOG.debug('    - Cluster %s : %s (%s)' % (i, cluster_id, CLUSTERS.get(cluster_id, 'unknown')))
            ZGT_LOG.debug('  - OUT cluster count  : {}'.format(msg['out_cluster_count']))
            for i, cluster_id in enumerate(msg['out_cluster_list']):
                ZGT_LOG.debug('    - Cluster %s : %s (%s)' % (i, cluster_id, CLUSTERS.get(cluster_id, 'unknown')))
            return True

        # Power Descriptor
        if msg_type == b'8044':
            struct = OrderedDict([('sequence', 8), ('status', 8),
                                  ('bit_field', 16), ])
            msg = zigate.decode_struct(struct, msg_data)

            bit_field_binary = format(int(msg['bit_field'], 16), '016b')

            # Others Reserved
            power_mode_desc = {'0000': 'Receiver on when idle',
                               '0001': 'Receiver switched on periodically',
                               '0010': 'Receiver switched on when stimulated,'}
            power_sources = ['Permanent mains supply', 'Rechargeable battery',
                             'Disposable battery']  # 4th Reserved
            current_power_level = {'0000': 'Critically low',
                                   '0100': 'Approximately 33%',
                                   '1000': 'Approximately 66%',
                                   '1100': 'Approximately 100%'}

            ZGT_LOG.debug('RESPONSE 8044 : Power Descriptor')
            ZGT_LOG.debug('  - Sequence          : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status            : {}'.format(msg['status']))
            ZGT_LOG.debug('  - Bit field         : {}'.format(msg['bit_field']))
            ZGT_LOG.debug('    - Binary          : {}'.format(bit_field_binary))
            ZGT_LOG.debug('    - Current mode    : {}'.format(
                power_mode_desc.get(bit_field_binary[-4:], 'Unknown')))
            ZGT_LOG.debug('    - Sources         : ')
            for i, description in enumerate(power_sources, 1):
                ZGT_LOG.debug('       - %s : %s %s' %
                              (description,
                               'Yes' if bit_field_binary[8:12][-i] == '1' else 'No',
                               '[CURRENT]' if bit_field_binary[4:8][-i] == '1' else '')
                              )
            ZGT_LOG.debug('    - Level           : {}'.format(
                current_power_level.get(bit_field_binary[:4], 'Unknown')))
            return True

        # Active Endpoint
        if msg_type == b'8045':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('endpoint_count', 'count'),
                                  ('endpoint_list', 8)])
            msg = zigate.decode_struct(struct, msg_data)
            endpoints = [elt.decode() for elt in msg['endpoint_list']]
            zigate.set_external_command(ZGT_CMD_LIST_ENDPOINTS, addr=msg['addr'].decode(), endpoints=endpoints)

            ZGT_LOG.debug('RESPONSE 8045 : Active Endpoints List')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))
            ZGT_LOG.debug('  - From address   : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - EndPoint count : {}'.format(msg['endpoint_count']))
            for i, endpoint in enumerate(msg['endpoint_list']):
                ZGT_LOG.debug('    * EndPoint %s : %s' % (i, endpoint))
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Description commands sending.
    """
    def network_adress(self, device_address, extended_address, start_index=0, extended=False):
        """
        Network Address request

        :param device_address: length 4
        :param extended_address: length 8
        :param start_index: int
        :param extended: bool
        """
        msg = device_address
        msg += extended_address
        msg += '{:02x}'.format(1 if extended else 0)
        msg += '{:02x}'.format(start_index)
        self.send_data('0040', msg)

    def ieee_adress(self, device_address, start_index=0, extended=False):
        """
        IEEE Address request

        :param device_address: length 4
        :param start_index: int
        :param extended: bool
        """
        msg = device_address + self.address_mode
        msg += '{:02x}'.format(1 if extended else 0)
        msg += '{:02x}'.format(start_index)
        self.send_data('0041', msg)

    def node_descriptor(self, device_address):
        """
        Node Descriptor request

        :param device_address: length 4
        """
        self.send_data('0042', device_address)

    def simple_descriptor(self, device_address, device_endpoint='01'):
        """
        Node Descriptor request

        :param device_address: length 4
        :param str device_endpoint: length 2, default to '01'
        """
        self.send_data('0043', device_address + device_endpoint)

    def power_descriptor(self, device_address):
        """
        Power Descriptor request

        :param device_address: length 4
        """
        self.send_data('0044', device_address)

    def endpoint_descriptor(self, device_address):
        """
        Power Descriptor request

        :param device_address: length 4
        """
        self.send_data('0045', device_address)
