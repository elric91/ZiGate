import logging
from binascii import hexlify, unhexlify
from collections import OrderedDict
from .abstract_feature import AbstractFeature, CLUSTERS
from ..zgt_parameters import *

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0000'

    def get_name(self):
        return 'General: Basic'

    def decode_msg(self, zigate, msg_type, msg_data):
        # Device Announce
        if msg_type == b'004d':
            struct = OrderedDict([('short_addr', 16), ('mac_addr', 64),
                                  ('mac_capability', 'rawend')])
            msg = zigate.decode_struct(struct, msg_data)

            zigate.set_external_command(ZGT_CMD_NEW_DEVICE, addr=msg['short_addr'].decode())
            zigate.set_device_property(msg['short_addr'], None, 'MAC', msg['mac_addr'].decode())

            ZGT_LOG.debug('RESPONSE 004d : Device Announce')
            ZGT_LOG.debug('  * From address   : {}'.format(msg['short_addr']))
            ZGT_LOG.debug('  * MAC address    : {}'.format(msg['mac_addr']))
            ZGT_LOG.debug('  * MAC capability : {}'.format(msg['mac_capability']))
            return True

        # “Permit join” status response
        if msg_type == b'8014':
            struct = OrderedDict([('status', 1)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 004d : “Permit join” status : {}'.format(msg['status']))
            return True

        # Device list
        if msg_type == b'8015':
            ZGT_LOG.debug('RESPONSE : Version List')

            while True:
                struct = OrderedDict([('ID', 8), ('addr', 16), ('IEEE', 64), ('power_source', 'int8'),
                                      ('link_quality', 'int8'), ('next', 'rawend')])
                msg = zigate.decode_struct(struct, msg_data)
                zigate.set_external_command(ZGT_CMD_LIST_DEVICES, **msg)
                ZGT_LOG.debug('  * deviceID     : {}'.format(msg['ID']))
                ZGT_LOG.debug('  - addr         : {}'.format(msg['addr']))
                ZGT_LOG.debug('  - IEEE         : {}'.format(msg['IEEE']))
                ZGT_LOG.debug('  - Power Source : {}'.format(msg['power_source']))
                ZGT_LOG.debug('  - Link Quality : {}'.format(msg['link_quality']))
                if len(msg['next']) < 13:
                    break
                else:
                    msg_data = msg['next']
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

        # Cluster List
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

        # Endpoint List
        if msg_type == b'8045':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('endpoint_count', 'count'),
                                  ('endpoint_list', 8)])
            msg = zigate.decode_struct(struct, msg_data)
            endpoints = [elt.decode() for elt in msg['endpoint_list']]
            # self.set_device_property(msg['addr'], None, 'endpoints', endpoints)
            zigate.set_external_command(ZGT_CMD_LIST_ENDPOINTS, addr=msg['addr'].decode(), endpoints=endpoints)

            ZGT_LOG.debug('RESPONSE 8045 : Active Endpoints List')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))
            ZGT_LOG.debug('  - From address   : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - EndPoint count : {}'.format(msg['endpoint_count']))
            for i, endpoint in enumerate(msg['endpoint_list']):
                ZGT_LOG.debug('    * EndPoint %s : %s' % (i, endpoint))
            return True

        # Leave indication
        if msg_type == b'8048':
            struct = OrderedDict([('extended_addr', 64), ('rejoin_status', 8)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8048 : Leave indication')
            ZGT_LOG.debug('  - From address   : {}'.format(msg['extended_addr']))
            ZGT_LOG.debug('  - Rejoin status  : {}'.format(msg['rejoin_status']))
            return True

        # Zone status change
        if msg_type == b'8401':
            struct = OrderedDict([('sequence', 8), ('endpoint', 8),
                                  ('cluster', 16), ('src_address_mode', 8),
                                  ('src_address', 16), ('zone_status', 16),
                                  ('extended_status', 16), ('zone_id', 8),
                                  ('delay_count', 'count'), ('delay_list', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            zone_status_binary = format(int(msg['zone_status'], 16), '016b')

            # Length 16, 10-15 Reserved
            zone_status_descs = ('Alarm 1', 'Alarm 2', 'Tampered',
                                 'Battery', 'Supervision reports',
                                 'Report when normal', 'Trouble',
                                 'AC (Mains)', 'Test Mode',
                                 'Battery defective')
            zone_status_values = (('Closed/Not alarmed', 'Opened/Alarmed'),
                                  ('Closed/Not alarmed', 'Opened/Alarmed'),
                                  ('No', 'Yes'), ('OK', 'Low'), ('No', 'Yes'),
                                  ('No', 'Yes'), ('No', 'Yes'),
                                  ('Ok', 'Failure'), ('No', 'Yes'),
                                  ('No', 'Yes'),)

            ZGT_LOG.debug('RESPONSE 8401 : Zone status change notification')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - EndPoint       : {}'.format(msg['endpoint']))
            ZGT_LOG.debug('  - Cluster id     : {} ({})'.format(
                msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            ZGT_LOG.debug('  - Src addr mode  : {}'.format(msg['src_address_mode']))
            ZGT_LOG.debug('  - Src address    : {}'.format(msg['src_address']))
            ZGT_LOG.debug('  - Zone status    : {}'.format(msg['zone_status']))
            ZGT_LOG.debug('    - Binary       : {}'.format(zone_status_binary))
            for i, description in enumerate(zone_status_descs, 1):
                j = int(zone_status_binary[-i])
                ZGT_LOG.debug('    - %s : %s' % (description, zone_status_values[i-1][j]))
            ZGT_LOG.debug('  - Zone id        : {}'.format(msg['zone_id']))
            ZGT_LOG.debug('  - Delay count    : {}'.format(msg['delay_count']))
            for i, value in enumerate(msg['delay_list']):
                ZGT_LOG.debug('    - %s : %s' % (i, value))
            return True

        # Route Discovery Confirmation
        if msg_type == b'8701':
            ZGT_LOG.debug('RESPONSE 8701: Route Discovery Confirmation')
            ZGT_LOG.debug('  - Sequence       : {}'.format(hexlify(msg_data[:1])))
            ZGT_LOG.debug('  - Status         : {}'.format(hexlify(msg_data[1:2])))
            ZGT_LOG.debug('  - Network status : {}'.format(hexlify(msg_data[2:3])))
            ZGT_LOG.debug('  - Message data   : {}'.format(hexlify(msg_data)))
            return True

        return False

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        if attr_id == b'0005':
            zigate.set_device_property(device_addr, endpoint, 'type', data.decode())
            ZGT_LOG.info(' * type : {}'.format(data))
            return True

        ## proprietary Xiaomi info including battery
        if attr_id == b'ff01' and data != b'':
            struct = OrderedDict([('start', 16), ('battery', 16), ('end', 'rawend')])
            raw_info = unhexlify(zigate.decode_struct(struct, data)['battery'])
            battery_info = int(hexlify(raw_info[::-1]), 16)/1000
            zigate.set_device_property(device_addr, endpoint, 'battery', battery_info)
            ZGT_LOG.info('  * Battery info')
            ZGT_LOG.info('  * Value : {} V'.format(battery_info))
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for commons command sending.
    """
    def permit_join(self, join_time=30):
        """
        permit join for join_time secs

        :type self: Zigate
        :type join_time: int
        """
        self.send_data("0049", "FFFC"+'{:02x}'.format(join_time)+"00")

    def permit_join_status(self):
        """
        permit join status

        :type self: Zigate
        """
        self.send_data("0014")

    def auth_devices_list(self):
        """
        Get auth devices list

        :type self: Zigate
        """
        self.send_data("0015")
