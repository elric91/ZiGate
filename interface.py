#! /usr/bin/python3
import serial
import threading
from binascii import (hexlify, unhexlify)
from time import (sleep, strftime)
from collections import OrderedDict


CLUSTERS = {b'0000':'General: Basic',
            b'0001':'General: Power Config',
            b'0002':'General: Temperature Config',
            b'0003':'General: Identify',
            b'0004':'General: Groups',
            b'0005':'General: Scenes',
            b'0006':'General: On/Off',
            b'0007':'General: On/Off Config',
            b'0008':'General: Level Control',
            b'0009':'General: Alarms',
            b'000A':'General: Time',
            b'000F':'General: Binary Input Basic',
            b'0020':'General: Poll Control',
            b'0019':'General: OTA',
            b'0101':'General: Door Lock',
            b'0201':'HVAC: Thermostat',
            b'0202':'HVAC: Fan Control',
            b'0300':'Lighting: Color Control',
            b'0400':'Measurement: Illuminance',
            b'0402':'Measurement: Temperature',
            b'0403':'Measurement: Atmospheric Pressure',
            b'0405':'Measurement: Humidity',
            b'0406':'Measurement: Occupancy Sensing',
            b'0500':'Security & Safety: IAS Zone',
            b'0702':'Smart Energy: Metering',
            b'0B05':'Misc: Diagnostics',
            b'1000':'ZLL: Commissioning',
            b'FF01':'Xiaomi private',
            b'FF02':'Xiaomi private'
          }

LOG_LEVELS = ['Emergency', 'Alert', 'Critical', 'Error', 'Warning', 'Notice', 'Information', 'Debug']


class ZiGate():

    def __init__(self, device="/dev/ttyUSB0"):
        self.conn = serial.Serial(device, 115200, timeout=0)
        self.buffer = b''
        self.thread = threading.Thread(target=self.read_data).start()
        self.devices = {}

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
            elif encoded == True:
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

    def set_device_property(self, addr, property_id, property_data):
        """
        log property / attribute value in a device based dictionnary
        please note that short addr is not stable if device is reset (still have to find the unique ID)
        """
        if not addr in self.devices:
            self.devices[addr] = {}
        self.devices[addr][property_id] = property_data

    def read_data(self):
        """Read ZiGate output and split messages"""
        while (True):
            bytesavailable = self.conn.inWaiting()
            if (bytesavailable > 0):
                self.buffer += self.conn.read(bytesavailable)
                endpos = self.buffer.find(b'\x03')
                if endpos != -1:
                    startpos = self.buffer.find(b'\x01')
                    data_to_decode = self.zigate_decode(self.buffer[startpos + 1:endpos]) # stripping starting 0x01 & ending 0x03
                    self.interpret_data(data_to_decode) 
                    print('  # encoded : ', hexlify(self.buffer[startpos:endpos + 1]))
                    print('  # decoded : 01', ' '.join([format(x, '02x') for x in data_to_decode]).upper(),'03')
                    print('  (@timestamp : ', strftime("%H:%M:%S"), ')')
                    self.buffer = self.buffer[endpos + 1:]

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
        if data != "": std_msg.extend(byte_data)
        std_msg.append(0x03)

        # --- encoded version ---
        enc_msg = [0x01]
        enc_msg.extend(self.zigate_encode(byte_cmd))
        enc_msg.extend(self.zigate_encode(byte_length))
        enc_msg.append(self.checksum(byte_cmd, byte_length, byte_data))
        if data != "": enc_msg.extend(self.zigate_encode(byte_data))
        enc_msg.append(0x03)

        std_output = b''.join([bytes([x]) for x in std_msg])
        encoded_output = b''.join([bytes([x]) for x in enc_msg])
        print('--------------------------------------')
        print('REQUEST      : ', cmd, " ", data)
        print('  # standard : ', ' '.join([format(x, '02x') for x in std_output]).upper())
        print('  # encoded  : ', hexlify(encoded_output))
        print('(timestamp : ', strftime("%H:%M:%S"), ')')
        print('--------------------------------------')
        self.conn.write(encoded_output)

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
            # element gives length of next element in message (which could be raw)
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
            # element gives number of next elements (which can be of a defined length)
            elif elt_type == 'count':
                count = int(hexlify(msg[:1]), 16)
                output[key] = count
                msg = msg[1:]
                # let's get the next element (list of elements referenced by the count)
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


    def interpret_data(self, data):
        """Interpret responses attributes"""
        msg_data = data[5:]
        msg_type = hexlify(data[0:2])

        # Do different things based on MsgType
        print('--------------------------------------')
        # Device Announce
        if msg_type == b'004d':
            struct = OrderedDict([('short_addr', 16), ('mac_addr', 64), ('mac_capability', 'rawend')])
            msg = self.decode_struct(struct, msg_data)

            self.set_device_property(msg['short_addr'], 'MAC', msg['mac_addr'])
            print('RESPONSE 004d : Device Announce')
            print('  * From address   : ', msg['short_addr'])
            print('  * MAC address    : ', msg['mac_addr'])
            print('  * MAC capability : ', msg['mac_capability'])
        
        # Status
        elif msg_type == b'8000':
            struct = OrderedDict([('status', 'int'), ('sequence', 8), ('packet_type', 16), ('info', 'rawend')])
            msg = self.decode_struct(struct, msg_data)

            if msg['status'] == 0:
                status_text = 'Success'
            elif msg['status'] == 1:
                status_text = 'Invalid parameters'
            elif msg['status'] == 2:
                status_text = 'Unhandled command'
            elif msg['status'] == 3:
                status_text = 'Command failed'
            elif msg['status'] == 4:
                status_text = 'Busy'
            elif msg['status'] == 5:
                status_text = 'Stack already started'
            elif msg['status'] >= 128:
                status_text = 'Failed with event code: %i' % msg['status']
            else:
                status_text = 'Unknown'

            print('RESPONSE 8000 : Status')
            print('  * Status              : ', status_text)
            print('  - Sequence            : ', msg['sequence'])
            print('  - Response to command : ', msg['packet_type'])
            if hexlify(msg['info']) != b'00':
                print('  - Additional msg: ', msg['info']) 
        
        # Default Response
        elif msg_type == b'8001':
            struct = OrderedDict([('level', 'int'), ('info', 'rawend')])
            msg = self.decode_struct(struct, msg_data)

            print('RESPONSE 8001 : Log Message')
            print('  - Log Level : Log level ', LOG_LEVELS[msg['level']])
            print('  - Log Info  : ', msg['info'])
        
        # Version List
        elif msg_type == b'8010':
            struct = OrderedDict([('major', 'int16'), ('installer', 'int16')])
            msg = self.decode_struct(struct, msg_data)

            print('RESPONSE : Version List')
            print('  - Major version : ', msg['major'])
            print('  - Installer version : ', msg['installer'])
        
        # Cluster List
        elif msg_type == b'8043':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16), ('length', 8),
                                  ('endpoint', 8), ('profile', 16), ('device_id', 16), ('bit', 8),
                                  ('in_cluster_count', 'count'), ('in_cluster_list', 16),
                                  ('out_cluster_count', 'count'), ('out_cluster_list', 16),
                                  ])
            msg = self.decode_struct(struct, msg_data)

            print('RESPONSE 8043 : Cluster List')
            print('  - Sequence          : ', msg['sequence'])
            print('  - Status            : ', msg['status'])
            print('  - From address      : ', msg['addr'])
            print('  - Length            : ', msg['length'])
            print('  - EndPoint          : ', msg['endpoint'])
            print('  - Profile ID        : ', msg['profile'])
            print('  - Device ID         : ', msg['device_id'])
            print('  - IN cluster count  : ', msg['in_cluster_count'])
            for i, cluster_id in enumerate(msg['in_cluster_list']):
                print('    - Cluster %s : %s (%s)' %(i, cluster_id, CLUSTERS.get(cluster_id, 'unknown')))
            print('  - OUT cluster count  : ', msg['out_cluster_count'])
            for i, cluster_id in enumerate(msg['in_cluster_list']):
                print('    - Cluster %s : %s (%s)' %(i, cluster_id, CLUSTERS.get(cluster_id, 'unknown')))

        # Endpoint List
        elif msg_type == b'8045':
            struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16), ('endpoint_count', 'count'),
                                  ('endpoint_list', 8)
                                  ])
            msg = self.decode_struct(struct, msg_data)

            print('RESPONSE 8045 : Active Endpoints List')
            print('  - Sequence       : ', msg['sequence'])
            print('  - Status         : ', msg['status'])
            print('  - From address   : ', msg['addr'])
            print('  - EndPoint count : ', msg['enpoint_count'])
            for i,endpoint in enumerate(msg['endpoint_list']):
                print('    * EndPoint %s : %s' % (i, endpoint))

        # Default Response
        elif msg_type == b'8101':
            struct = OrderedDict([('sequence', 8), ('endpoint', 8), ('cluster', 16), ('command_id', 8),
                                  ('status', 8)
                                  ])
            msg = self.decode_struct(struct, msg_data)

            print('RESPONSE 8101 : Default Response')
            print('  - Sequence       : ', msg['sequence'])
            print('  - EndPoint       : ', msg['endpoint'])
            print('  - Cluster id     :  %s (%s)' % (msg['cluster'], CLUSTERS.get(msg['cluster'], 'unknown')))
            print('  - Command        : ', msg['command_id'])
            print('  - Status         : ', msg['status'])

        # Currently only support Xiaomi sensors. Other brands might calc things differently
        elif msg_type == b'8102':
            sequence = hexlify(data[5:6])
            self.interpret_attribute(msg_data)

        # Route Discovery Confirmation
        elif msg_type == b'8701':
            print('RESPONSE 8701: Route Discovery Confirmation')
            print('  - Sequence       : ', hexlify(msg_data[:1]))
            print('  - Status         : ', hexlify(msg_data[1:2]))
            print('  - Network status : ', hexlify(msg_data[2:3]))
            print('  - Message data   : ', hexlify(msg_data))
        
        # No handling for this type of message
        else:
            print('RESPONSE : Unknown Message')
            print('  - After decoding  : ', hexlify(data))
            print('  - MsgType         : ', msg_type)
            print('  - MsgLength       : ', hexlify(data[2:4]))
            print('  - ChkSum          : ', hexlify(data[4:5]))
            print('  - Data            : ', hexlify(msg_data))
            print('  - RSSI            : ', hexlify(data[-1:]))

    def interpret_attribute(self, msg_data):
        struct = OrderedDict([('sequence', 8),
                  ('short_addr', 16),
                  ('endpoint', 8),
                  ('cluster_id', 16),
                  ('attribute_id', 16),
                  ('attribute_status', 8),
                  ('attribute_type', 8),
                  ('attribute_size', 'len16'),
                  ('attribute_data', 'raw'),
                  ('end', 'rawend')
                 ])
        msg = self.decode_struct(struct, msg_data)
        device_addr = msg['short_addr']
        cluster_id = msg['cluster_id']
        attribute_id = msg['attribute_id']
        attribute_size = msg['attribute_size']
        attribute_data = msg['attribute_data']
        self.set_device_property(device_addr, (cluster_id,attribute_id), attribute_data) # register tech value
        self.set_device_property(device_addr, 'Last seen', strftime('%Y-%m-%d %H:%M:%S'))

        print('RESPONSE 8102 : Attribute Report')
        if msg['sequence'] == b'00':
            print('  - Sensor type announce (Start after pairing 1)')
        elif msg['sequence'] == b'01':
            print('  - Something announce (Start after pairing 2)')

        # Device type
        if cluster_id == b'0000':
            if attribute_id == b'0005':
                self.set_device_property(device_addr, 'Type', attribute_data)
                print(' * type : ', attribute_data)
        # Button status
        elif cluster_id == b'0006':
            print('  * General: On/Off')
            if attribute_id == b'0000':
                if attribute_data == b'00':
                    print('  * Closed/Taken off/Press')
                else:
                    print('  * Open/Release button')
            elif attribute_id == b'8000':
                print('  * Multi click')
                print('  * Pressed: ', int(hexlify(attribute_data), 16), " times")
        elif cluster_id == b'000c':  # Unknown cluster id
            print('  * Rotation horizontal')
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if attribute_data == b'0000':
                    print('  * Shaking')
                elif attribute_data == b'0055':
                    print('  * Rotating vertical')
                    print('  * Rotated: ', int(hexlify(attribute_data), 16), "°")
                elif attribute_data == b'0103':
                    print('  * Sliding')
        elif cluster_id == b'0402':
            temperature = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, 'Temperature', temperature)
            print('  * Measurement: Temperature'),
            print('  * Value: ', temperature, "°C")
        elif cluster_id == b'0403':
            print('  * Atmospheric pressure')
            pressure = int(hexlify(attribute_data), 16)
            if attribute_id == b'0000':
                self.set_device_property(device_addr, 'Pressure', pressure)
                print('  * Value: ', pressure, "mb")
            elif attribute_id == b'0010':
                self.set_device_property(device_addr, 'Pressure - detailed', pressure/10)
                print('  * Value: ', pressure/10, "mb")
            elif attribute_id == b'0014':
                print('  * Value unknown')
        elif cluster_id == b'0405':
            humidity = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, 'Humidity', humidity)
            print('  * Measurement: Humidity')
            print('  * Value: ', humidity, "%")
        elif cluster_id == b'0406':
            print('   * Presence detection')  # Only sent when movement is detected

        print('  FROM ADDRESS      : ', msg['short_addr'])
        print('  - Source EndPoint : ', msg['endpoint'])
        print('  - Cluster ID      : ', msg['cluster_id'])
        print('  - Attribute ID    : ', msg['attribute_id'])
        print('  - Attribute type  : ', msg['attribute_type'])
        print('  - Attribute size  : ', msg['attribute_size'])
        print('  - Attribute data  : ', hexlify(msg['attribute_data']))

    def list_devices(self):
        print('-- DEVICE REPORT -------------------------')
        for addr in self.devices.keys():
            print('- addr : ', addr)
            for k,v in self.devices[addr].items():
                if type(k) is tuple:
                    print('    * ', k, ' : ', v,' (',CLUSTERS[k[0]],')')
                else:
                    print('    * ', k, ' : ', v) 
        print('-- DEVICE REPORT - END -------------------')

if __name__ == "__main__":
    zigate = ZiGate()
