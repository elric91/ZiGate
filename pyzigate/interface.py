#! /usr/bin/python3
import logging
from binascii import hexlify
from time import strftime
from collections import OrderedDict
from . import commands_helpers, attributes_helpers
from .zgt_parameters import *


CLUSTERS = {b'0000': 'General: Basic',
            b'0001': 'General: Power Config',
            b'0002': 'General: Temperature Config',
            b'0003': 'General: Identify',
            b'0004': 'General: Groups',
            b'0005': 'General: Scenes',
            b'0006': 'General: On/Off',
            b'0007': 'General: On/Off Config',
            b'0008': 'General: Level Control',
            b'0009': 'General: Alarms',
            b'000A': 'General: Time',
            b'000F': 'General: Binary Input Basic',
            b'0020': 'General: Poll Control',
            b'0019': 'General: OTA',
            b'0101': 'General: Door Lock',
            b'0201': 'HVAC: Thermostat',
            b'0202': 'HVAC: Fan Control',
            b'0300': 'Lighting: Color Control',
            b'0400': 'Measurement: Illuminance',
            b'0402': 'Measurement: Temperature',
            b'0403': 'Measurement: Atmospheric Pressure',
            b'0405': 'Measurement: Humidity',
            b'0406': 'Measurement: Occupancy Sensing',
            b'0500': 'Security & Safety: IAS Zone',
            b'0702': 'Smart Energy: Metering',
            b'0B05': 'Misc: Diagnostics',
            b'1000': 'ZLL: Commissioning',
            b'FF01': 'Xiaomi private',
            b'FF02': 'Xiaomi private'
            }

ZGT_LOG = logging.getLogger('zigate')


class ZiGate(commands_helpers.Mixin, attributes_helpers.Mixin):

    def __init__(self):
        self._buffer = b''
        self._devices_info = {}

    @staticmethod
    def zigate_encode(data):
        """encode all characters < 0x02 to avoid """
        encoded = []
        for x in data:
            if x < 0x10:
                encoded.append(0x02)
                encoded.append(x ^ 0x10)
            else:
                encoded.append(x)

        return encoded

    @staticmethod
    def zigate_decode(data):
        """reverse of zigate_encode to get back the real message"""
        encoded = False
        decoded_data = b''

        def bxor_join(b1, b2):  # use xor for bytes
            parts = []
            for b1, b2 in zip(b1, b2):
                parts.append(bytes([b1 ^ b2]))
            return b''.join(parts)

        for x in data:
            if bytes([x]) == b'\x02':
                encoded = True
            elif encoded is True:
                encoded = False
                decoded_data += bxor_join(bytes([x]), b'\x10')
            else:
                decoded_data += bytes([x])

        return decoded_data

    @staticmethod
    def checksum(cmd, length, data):
        tmp = 0
        tmp ^= cmd[0]
        tmp ^= cmd[1]
        tmp ^= length[0]
        tmp ^= length[1]
        if data:
            for x in data:
                tmp ^= x

        return tmp

    # register valuable (i.e. non technical properties) for futur use
    def set_device_property(self, addr, endpoint, property_id, property_data):
        """
        log property / attribute value in a device based dictionnary
        please note that short addr is not stable if device is reset
        (still have to find the unique ID)
        all data stored must be directly usable (i.e no bytes)
        """
        if endpoint:
            str_addr = '{}_{}'.format(addr.decode(), endpoint.decode())
        else:
            str_addr = '{}_x'.format(addr.decode())
        if str_addr not in self._devices_info:
            self._devices_info[str_addr] = {}
        self._devices_info[str_addr][property_id] = property_data

    # Must be overridden by external program
    def set_external_command(self, command_type, **kwargs):
        pass

    # Must be defined and assigned in the transport object
    @staticmethod
    def send_to_transport(data):
        pass

    # Must be called from a thread loop or asyncio event loop
    def read_data(self, data):
        """Read ZiGate output and split messages"""
        self._buffer += data
        endpos = self._buffer.find(b'\x03')
        while endpos != -1:
            startpos = self._buffer.find(b'\x01')
            # stripping starting 0x01 & ending 0x03
            data_to_decode = self.zigate_decode(self._buffer[startpos + 1:endpos])
            self.decode_data(data_to_decode)
            ZGT_LOG.debug('  # encoded : {}'.format(hexlify(self._buffer[startpos:endpos + 1])))
            ZGT_LOG.debug('  # decoded : 01{}03'.format(
                ' '.join([format(x, '02x') for x in data_to_decode]).upper()))
            ZGT_LOG.debug('  (@timestamp : {})'.format(strftime("%H:%M:%S")))
            self._buffer = self._buffer[endpos + 1:]
            endpos = self._buffer.find(b'\x03')

    # Calls "transport_write" which must be defined
    # in a serial connection or pyserial_asyncio transport
    def send_data(self, cmd, data=""):
        """send data through ZiGate"""
        byte_cmd = bytes.fromhex(cmd)
        byte_data = bytes.fromhex(data)
        length = int(len(data)/2)
        byte_length = length.to_bytes(2, 'big')

        # --- non encoded version ---
        std_msg = [0x01]
        std_msg.extend(byte_cmd)
        std_msg.extend(byte_length)
        std_msg.append(self.checksum(byte_cmd, byte_length, byte_data))
        if data != "":
            std_msg.extend(byte_data)
        std_msg.append(0x03)

        # --- encoded version ---
        enc_msg = [0x01]
        enc_msg.extend(self.zigate_encode(byte_cmd))
        enc_msg.extend(self.zigate_encode(byte_length))
        enc_msg.append(self.checksum(byte_cmd, byte_length, byte_data))
        if data != "":
            enc_msg.extend(self.zigate_encode(byte_data))
        enc_msg.append(0x03)

        std_output = b''.join([bytes([x]) for x in std_msg])
        encoded_output = b''.join([bytes([x]) for x in enc_msg])
        ZGT_LOG.debug('--------------------------------------')
        ZGT_LOG.debug('REQUEST      : {} {}'.format(cmd, data))
        ZGT_LOG.debug('  # standard : {}'.format(' '.join([format(x, '02x') for x in std_output]).upper()))
        ZGT_LOG.debug('  # encoded  : {}'.format(hexlify(encoded_output)))
        ZGT_LOG.debug('(timestamp : {})'.format(strftime("%H:%M:%S")))
        ZGT_LOG.debug('--------------------------------------')

        self.send_to_transport(encoded_output)

    @staticmethod
    def decode_struct(struct, msg):
        output = OrderedDict()
        while struct:
            key, elt_type = struct.popitem(last=False)
            # uint_8, 16, 32, 64 ... or predefined byte length
            if type(elt_type) == int:
                length = int(elt_type / 8)
                output[key] = hexlify(msg[:length])
                msg = msg[length:]
            # int (1 ou 2 bytes)
            elif elt_type in ('int', 'int8', 'int16'):
                if elt_type == 'int16':
                    index = 2
                else:
                    index = 1
                output[key] = int(hexlify(msg[:index]), 16)
                msg = msg[index:]
            # element gives length of next element in message
            # (which could be raw)
            elif elt_type in ('len8', 'len16'):
                if elt_type == 'len16':
                    index = 2
                else:
                    index = 1
                length = int(hexlify(msg[0:index]), 16)
                output[key] = length
                msg = msg[index:]
                # let's get the next element
                key, elt_type = struct.popitem(last=False)
                if elt_type == 'raw':
                    output[key] = msg[:length]
                    msg = msg[length:]
                else:
                    output[key] = hexlify(msg[:length])
                    msg = msg[length:]
            # element gives number of next elements
            # (which can be of a defined length)
            elif elt_type == 'count':
                count = int(hexlify(msg[:1]), 16)
                output[key] = count
                msg = msg[1:]
                # let's get the next element
                # (list of elements referenced by the count)
                key, elt_type = struct.popitem(last=False)
                output[key] = []
                length = int(elt_type / 8)
                for i in range(count):
                    output[key].append(hexlify(msg[:length]))
                    msg = msg[length:]
            # remaining of the message
            elif elt_type == 'end':
                output[key] = hexlify(msg)
            # remaining of the message as raw data
            elif elt_type == 'rawend':
                output[key] = msg

        return output

    def decode_data(self, data):
        """Interpret responses attributes"""
        msg_data = data[5:]
        msg_type = hexlify(data[0:2])

        # Do different things based on MsgType
        ZGT_LOG.debug('--------------------------------------')
        # Device Announce
        if msg_type == b'004d':
            struct = OrderedDict([('short_addr', 16), ('mac_addr', 64),
                                  ('mac_capability', 'rawend')])
            msg = self.decode_struct(struct, msg_data)

            self.set_external_command(ZGT_CMD_NEW_DEVICE, addr=msg['short_addr'].decode())
            self.set_device_property(msg['short_addr'], None, 'MAC', msg['mac_addr'].decode())

            ZGT_LOG.debug('RESPONSE 004d : Device Announce')
            ZGT_LOG.debug('  * From address   : {}'.format(msg['short_addr']))
            ZGT_LOG.debug('  * MAC address    : {}'.format(msg['mac_addr']))
            ZGT_LOG.debug('  * MAC capability : {}'.format(msg['mac_capability']))

        # Status
        elif msg_type == b'8000':
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

        # Default Response
        elif msg_type == b'8001':
            zgt_log_levels = ['Emergency', 'Alert', 'Critical', 'Error',
                              'Warning', 'Notice', 'Information', 'Debug']
            struct = OrderedDict([('level', 'int'), ('info', 'rawend')])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8001 : Log Message')
            ZGT_LOG.debug('  - Log Level : {}'.format(zgt_log_levels[msg['level']]))
            ZGT_LOG.debug('  - Log Info  : {}'.format(msg['info']))

        # Version List
        elif msg_type == b'8010':
            struct = OrderedDict([('major', 'int16'), ('installer', 'int16')])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE : Version List')
            ZGT_LOG.debug('  - Major version     : {}'.format(msg['major']))
            ZGT_LOG.debug('  - Installer version : {}'.format(msg['installer']))

        # Node Descriptor
        elif msg_type == b'8042':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('manufacturer_code', 16),
                                  ('max_rx', 16), ('max_tx', 16),
                                  ('server_mask', 16),
                                  ('descriptor_capability', 8),
                                  ('mac_flags', 8), ('max_buffer_size', 16),
                                  ('bit_field', 16)])
            msg = self.decode_struct(struct, msg_data)

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

        # Cluster List
        elif msg_type == b'8043':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('length', 8), ('endpoint', 8),
                                  ('profile', 16), ('device_id', 16),
                                  ('bit', 8), ('in_cluster_count', 'count'),
                                  ('in_cluster_list', 16),
                                  ('out_cluster_count', 'count'),
                                  ('out_cluster_list', 16)])
            msg = self.decode_struct(struct, msg_data)

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

        # Power Descriptor
        elif msg_type == b'8044':
            struct = OrderedDict([('sequence', 8), ('status', 8),
                                 ('bit_field', 16), ])
            msg = self.decode_struct(struct, msg_data)

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

        # Endpoint List
        elif msg_type == b'8045':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                                  ('endpoint_count', 'count'),
                                  ('endpoint_list', 8)])
            msg = self.decode_struct(struct, msg_data)
            endpoints = [elt.decode() for elt in msg['endpoint_list']]
            # self.set_device_property(msg['addr'], None, 'endpoints', endpoints)
            self.set_external_command(ZGT_CMD_LIST_ENDPOINTS, addr=msg['addr'].decode(), endpoints=endpoints)

            ZGT_LOG.debug('RESPONSE 8045 : Active Endpoints List')
            ZGT_LOG.debug('  - Sequence       : {}'.format(msg['sequence']))
            ZGT_LOG.debug('  - Status         : {}'.format(msg['status']))
            ZGT_LOG.debug('  - From address   : {}'.format(msg['addr']))
            ZGT_LOG.debug('  - EndPoint count : {}'.format(msg['endpoint_count']))
            for i, endpoint in enumerate(msg['endpoint_list']):
                ZGT_LOG.debug('    * EndPoint %s : %s' % (i, endpoint))

        # Leave indication
        elif msg_type == b'8048':
            struct = OrderedDict([('extended_addr', 64), ('rejoin_status', 8)])
            msg = self.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8048 : Leave indication')
            ZGT_LOG.debug('  - From address   : {}'.format(msg['extended_addr']))
            ZGT_LOG.debug('  - Rejoin status  : {}'.format(msg['rejoin_status']))

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

        # Read attribute response, Attribute report, Write attribute response
        # Currently only support Xiaomi sensors.
        # Other brands might calc things differently
        elif msg_type in (b'8100', b'8102', b'8110'):
            ZGT_LOG.debug('RESPONSE %s : Attribute Report / Response' % msg_type.decode())
            self.interpret_attributes(msg_data)

        # Zone status change
        elif msg_type == b'8401':
            struct = OrderedDict([('sequence', 8), ('endpoint', 8),
                                 ('cluster', 16), ('src_address_mode', 8),
                                 ('src_address', 16), ('zone_status', 16),
                                 ('extended_status', 16), ('zone_id', 8),
                                 ('delay_count', 'count'), ('delay_list', 16)])
            msg = self.decode_struct(struct, msg_data)

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

        # Route Discovery Confirmation
        elif msg_type == b'8701':
            ZGT_LOG.debug('RESPONSE 8701: Route Discovery Confirmation')
            ZGT_LOG.debug('  - Sequence       : {}'.format(hexlify(msg_data[:1])))
            ZGT_LOG.debug('  - Status         : {}'.format(hexlify(msg_data[1:2])))
            ZGT_LOG.debug('  - Network status : {}'.format(hexlify(msg_data[2:3])))
            ZGT_LOG.debug('  - Message data   : {}'.format(hexlify(msg_data)))

        # APS Data Confirm Fail
        elif msg_type == b'8702':
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

        # No handling for this type of message
        else:
            ZGT_LOG.debug('RESPONSE %s : Unknown Message' % msg_type.decode())
            ZGT_LOG.debug('  - After decoding  : {}'.format(hexlify(data)))
            ZGT_LOG.debug('  - MsgType         : {}'.format(msg_type))
            ZGT_LOG.debug('  - MsgLength       : {}'.format(hexlify(data[2:4])))
            ZGT_LOG.debug('  - ChkSum          : {}'.format(hexlify(data[4:5])))
            ZGT_LOG.debug('  - Data            : {}'.format(hexlify(msg_data)))
            ZGT_LOG.debug('  - RSSI            : {}'.format(hexlify(data[-1:])))

