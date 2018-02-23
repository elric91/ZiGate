#! /usr/bin/python3
import logging
from binascii import hexlify
from time import strftime
from collections import OrderedDict

from pyzigate.zgt_parameters import ZGT_LAST_SEEN
from .features import zigate_feature, commons_feature, attributes_feature


FEATURES = [zigate_feature.Feature(),
            commons_feature.Feature(),
            attributes_feature.Feature()
            ]

ZGT_LOG = logging.getLogger('zigate')


class ZiGate(zigate_feature.CommandsMixin,
             commons_feature.CommandsMixin,
             attributes_feature.CommandsMixin):

    def __init__(self):
        self._buffer = b''
        self._devices_info = {}
        self.address_mode = '02'
        self.src_endpoint = '01'

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
        length = len(byte_data)
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
        msg_length = int.from_bytes(data[2:4], byteorder='big', signed=False)
        msg_crc = int.from_bytes(data[4:5], byteorder='big', signed=False)
        msg_rssi = int.from_bytes(data[-1:], byteorder='big', signed=False)

        if msg_length != len(msg_data) :
            ZGT_LOG.error('BAD LENGTH {0} != {1}'.format(msg_length,len(msg_data)))
            return

        computed_crc = self.checksum(data[0:2], data[2:4], data[5:])
        if msg_crc != computed_crc :
            ZGT_LOG.error('BAD CRC {0} != {1}'.format(msg_crc,computed_crc))
            return

        processed = False

        # Do different things based on MsgType
        ZGT_LOG.debug('--------------------------------------')

        # Read attribute response, Attribute report, Write attribute response
        if msg_type in (b'8100', b'8102', b'8110'):
            ZGT_LOG.debug('RESPONSE %s : Attribute Report / Response' % msg_type.decode())
            struct = OrderedDict([('sequence', 8),
                                  ('short_addr', 16),
                                  ('endpoint', 8),
                                  ('cluster_id', 16),
                                  ('attribute_id', 16),
                                  ('attribute_status', 8),
                                  ('attribute_type', 8),
                                  ('attribute_size', 'len16'),
                                  ('attribute_data', 'raw'),
                                  ('end', 'rawend')])

            attr_msg = self.decode_struct(struct, msg_data)
            device_addr = attr_msg['short_addr']
            endpoint = attr_msg['endpoint']
            cluster_id = attr_msg['cluster_id']
            attribute_id = attr_msg['attribute_id']
            attribute_type = attr_msg['attribute_type']
            attribute_size = attr_msg['attribute_size']
            attribute_data = attr_msg['attribute_data']

            self.set_device_property(device_addr, endpoint, ZGT_LAST_SEEN, strftime('%Y-%m-%d %H:%M:%S'))

            if attr_msg['sequence'] == b'00':
                ZGT_LOG.debug('  - Sensor type announce (Start after pairing 1)')
            elif attr_msg['sequence'] == b'01':
                ZGT_LOG.debug('  - Something announce (Start after pairing 2)')

            if attr_msg['attribute_type'] != b'ff':
                if attr_msg['attribute_type'] == b'00':
                    # 0x00	Null
                    attr_val = None
                elif attr_msg['attribute_type'] == b'10':
                    # 0x10	boolean
                    attr_val = hexlify(attribute_data) != b'00'
                elif attr_msg['attribute_type'] == b'20' or \
                     attr_msg['attribute_type'] == b'21' or \
                     attr_msg['attribute_type'] == b'22' or \
                     attr_msg['attribute_type'] == b'25':
                    # 0x20	uint8	unsigned char
                    # 0x21	uint16
                    # 0x22	uint32
                    # 0x25	uint48
                    attr_val = int.from_bytes(attribute_data, 'big', signed=False)
                elif attr_msg['attribute_type'] == b'28' or \
                        attr_msg['attribute_type'] == b'29' or \
                        attr_msg['attribute_type'] == b'2a':
                    # 0x28	int8
                    # 0x29	int16
                    # 0x2a	int32
                    attr_val = int.from_bytes(attribute_data, 'big', signed=False)
                else:
                    # 0x18	8-bit bitmap
                    # 0x30	Enumeration : 8bit
                    # 0x42	string
                    try:
                        attr_val = attribute_data.decode()
                    except UnicodeDecodeError:
                        attr_val = attribute_data

                self.set_device_property(device_addr, endpoint,
                                         cluster_id.decode()+'_'+attribute_id.decode()+'_raw', attribute_data)
                self.set_device_property(device_addr, endpoint,
                                         cluster_id.decode()+'_'+attribute_id.decode(), attr_val)

            for feature in FEATURES:
                if feature.get_id() == cluster_id:
                    ZGT_LOG.info('  * {}'.format(feature.get_name()))
                    if feature.interprete_attribute(self, device_addr, endpoint, attribute_id, attribute_type, attribute_size, attribute_data):
                        processed = True

            if not processed:
                ZGT_LOG.info('  FROM ADDRESS      : {}'.format(device_addr))
                ZGT_LOG.debug('  - Source EndPoint : {}'.format(endpoint))
                ZGT_LOG.debug('  - Cluster ID      : {}'.format(cluster_id))
                ZGT_LOG.debug('  - Attribute ID    : {}'.format(attribute_id))
                ZGT_LOG.debug('  - Attribute type  : {}'.format(attribute_type))
                ZGT_LOG.debug('  - Attribute size  : {}'.format(attribute_size))
                ZGT_LOG.debug('  - Attribute data  : {}'.format(hexlify(attribute_data)))
            processed = True
        else:
            for feature in FEATURES:
                if feature.decode_msg(self, msg_type, msg_data):
                    processed = True

        # No handling for this type of message
        if not processed:
            ZGT_LOG.debug('RESPONSE %s : Unknown Message' % msg_type.decode())
            ZGT_LOG.debug('  - After decoding  : {}'.format(hexlify(data)))
            ZGT_LOG.debug('  - MsgType         : {}'.format(msg_type))
            ZGT_LOG.debug('  - MsgLength       : {}'.format(hexlify(data[2:4])))
            ZGT_LOG.debug('  - ChkSum          : {}'.format(hexlify(data[4:5])))
            ZGT_LOG.debug('  - Data            : {}'.format(hexlify(msg_data)))
            ZGT_LOG.debug('  - RSSI            : {}'.format(hexlify(data[-1:])))

