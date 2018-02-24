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
            ZGT_LOG.debug('RESPONSE : Device List')

            while True:
                struct = OrderedDict([('ID', 8), ('addr', 16), ('IEEE', 64), ('power_source', 'int8'),
                                      ('link_quality', 'int8'), ('next', 'rawend')])
                msg = zigate.decode_struct(struct, msg_data)
                zigate.set_external_command(ZGT_CMD_LIST_DEVICES, **msg)
                ZGT_LOG.debug(' -------------------------')
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

    def list_devices(self):
        """
        Get auth devices list

        :type self: Zigate
        """
        self.send_data("0015")

    def identify(self, device_address, duration=1, device_endpoint='01'):
        """
        Identification query

        :type self: Zigates
        :param str device_address: length 4
        :param duration: int in seconds
        :param str device_endpoint: length 2, default to '01'
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        if duration > 0:
            cmd += '{:04x}'.format(duration)
        self.send_data('0071' if duration <= 0 else '0070', cmd)
