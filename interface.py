#! /usr/bin/python3
import serial
import threading
import binascii
from time import (sleep, strftime)


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
                    data_to_decode = self.zigate_decode(self.buffer[startpos + 1:endpos])
                    print('RESPONSE (@timestamp : ', strftime("%H:%M:%S"), ')')
                    print('  - encoded : ', binascii.hexlify(self.buffer[startpos:endpos + 1]))
                    print('  - decoded : 01', ' '.join([format(x, '02x') for x in data_to_decode]).upper(),'03') 
                    self.interpret_data(data_to_decode)  # stripping starting 0x01 & ending 0x03
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
        print('  - standard : ', ' '.join([format(x, '02x') for x in std_output]).upper())
        print('  - encoded  : ', binascii.hexlify(encoded_output))
        print('(timestamp : ', strftime("%H:%M:%S"), ')')
        print('--------------------------------------')
        self.conn.write(encoded_output)

    def interpret_data(self, data):
        """Interpret responses attributes"""
        msg_data = data[6:]
        msg_type = binascii.hexlify(data[:2])

        # Do different things based on MsgType
        # Device Announce
        if binascii.hexlify(data[:2]) == b'004d':
            device_addr = binascii.hexlify(msg_data[:2])
            self.set_device_property(device_addr, 'MAC', binascii.hexlify(msg_data[2:10]))
            print('  - RESPONSE 004d : Device Announce')
            print('    * From address: ', device_addr)
            print('    * MAC address: ', binascii.hexlify(msg_data[2:10]))
            print('    * MAC capability: ', binascii.hexlify(msg_data[10:11]))
            print('    * Full data: ', binascii.hexlify(msg_data))
        # Status
        elif msg_type == b'8000':
            status_code = int(binascii.hexlify(data[5:6]), 16)
            if status_code == 0:
                status_text = 'Success'
            elif status_code == 1:
                status_text = 'Invalid parameters'
            elif status_code == 2:
                status_text = 'Unhandled command'
            elif status_code == 3:
                status_text = 'Command failed'
            elif status_code == 4:
                status_text = 'Busy'
            elif status_code == 5:
                status_text = 'Stack already started'
            elif status_code >= 128:
                status_text = 'Failed with event code: %i' % status_code
            else:
                status_text = 'Unknown'
            print('  - RESPONSE 8000 : Status')
            print('    * Status: ', status_text)
            print('    * Sequence: ', binascii.hexlify(data[6:7]))
            print('    * Response to command: ', binascii.hexlify(data[7:9]))
            if binascii.hexlify(data[9:]) != b'00':
                print('  *Additional msg: ', binascii.hexlify(data[9:])) 
        # Default Response
        elif msg_type == b'8001':
            log_level = int(binascii.hexlify(msg_data[:2]), 16)
            print(' - RESPONSE 8001 : Log Message')
            print('   *  : Log level ', LOG_LEVELS[log_level])
            print('   *  : ', binascii.hexlify(msg_data))
        # Version list
        elif msg_type == b'8010':
            print(' - RESPONSE : Version List')
            print('   * Major version : ', binascii.hexlify(data[6:8]))
            print('   * Installer version : ', binascii.hexlify(data[8:10]))
        # Endpoint list
        elif msg_type == b'8045':
            print(' - RESPONSE 8045 : Active Endpoint')
            print('   * Sequence : ', binascii.hexlify(data[6:8]))
        # Currently only support Xiaomi sensors. Other brands might calc things differently
        elif msg_type == b'8102':
            sequence = binascii.hexlify(data[5:6])
            print('  - RESPONSE 8102 : Attribute Report')
            if sequence == b'00':
                print('    * Sensor type announce (Start after pairing 1)')
            elif sequence == b'01':
                print('    * Something announce (Start after pairing 2)')
            self.interpret_attribute(msg_data)
        # Route Discovery Confirmation
        elif msg_type == b'8701':
            print(' - RESPONSE 8701: Route Discovery Confirmation')
            print('   * Sequence: ', binascii.hexlify(data[5:6]))
            print('   * Status: ', binascii.hexlify(msg_data[0:1]))
            print('   * Network status: ', binascii.hexlify(msg_data[1:2]))
            print('   * Full data: ', binascii.hexlify(msg_data))
        # No handling for this type of message
        else:
            print(' - RESPONSE : Unknown Message')
            print('   * After decoding  : ', binascii.hexlify(data))
            print('   * MsgType         : ', msg_type)
            print('   * MsgLength       : ', binascii.hexlify(data[2:4]))
            print('   * RSSI            : ', binascii.hexlify(data[4:5]))
            print('   * ChkSum          : ', binascii.hexlify(data[5:6]))
            print('   * Data            : ', binascii.hexlify(msg_data))

    def interpret_attribute(self, msg_data):
        device_addr = binascii.hexlify(msg_data[:2])
        cluster_id = binascii.hexlify(msg_data[3:5])
        attribute_id = binascii.hexlify(msg_data[5:7])
        attribute_size = int(binascii.hexlify(msg_data[9:11]), 16)  # Convert attribute size data to int
        attribute_data = binascii.hexlify(msg_data[11:11 + attribute_size])
        self.set_device_property(device_addr, (cluster_id,attribute_id), attribute_data) # register tech value
        self.set_device_property(device_addr, 'Last seen', strftime('%Y-%m-%d %H:%M:%S'))

        # Which attribute
        if cluster_id == b'0000':
            if attribute_id == b'0005':
                device_type = binascii.unhexlify(attribute_data)
                self.set_device_property(device_addr, 'Type', device_type)
                print('   * type : ', device_type)
        elif cluster_id == b'0006':
            print('    * General: On/Off')
            if attribute_id == b'0000':
                if attribute_data == b'00':
                    print('    * Closed/Taken off/Press')
                else:
                    print('    * Open/Release button')
            elif attribute_id == b'8000':
                print('    * Multi click')
                print('    * Pressed: ', int(attribute_data, 16), " times")
        elif cluster_id == b'000c':  # Unknown cluster id
            print('    * Rotation horizontal')
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if attribute_data == b'0000':
                    print('    * Shaking')
                elif attribute_data == b'0055':
                    print('    * Rotating vertical')
                    print('    * Rotated: ', int(attribute_data, 16), "°")
                elif attribute_data == b'0103':
                    print('    * Sliding')
        elif cluster_id == b'0402':
            temperature = int(attribute_data, 16) / 100
            self.set_device_property(device_addr, 'Temperature', temperature)
            print('    * Measurement: Temperature'),
            print('    * Value: ', temperature, "°C")
        elif cluster_id == b'0403':
            print('    * Atmospheric pressure')
            if attribute_id == b'0000':
                self.set_device_property(device_addr, 'Pressure', int(attribute_data, 16))
                print('    * Value: ', int(attribute_data, 16), "mb")
            elif attribute_id == b'0010':
                self.set_device_property(device_addr, 'Pressure - detailed', int(attribute_data, 16)/10)
                print('    * Value: ', int(attribute_data, 16)/10, "mb")
            elif attribute_id == b'0014':
                print('    * Value unknown')
        elif cluster_id == b'0405':
            humidity = int(attribute_data, 16) / 100
            self.set_device_property(device_addr, 'Humidity', humidity)
            print('    * Measurement: Humidity')
            print('    * Value: ', humidity, "%")
        elif cluster_id == b'0406':
            print('   * Presence detection')  # Only sent when movement is detected

        print('  - From address: ', device_addr)
        print('  - Source Ep: ', binascii.hexlify(msg_data[2:3]))
        print('  - Cluster ID: ', cluster_id)
        print('  - Attribute ID: ', attribute_id)
        print('  - Attribute size: ', binascii.hexlify(msg_data[9:11]))
        print('  - Attribute type: ', binascii.hexlify(msg_data[8:9]))
        print('  - Attribute data: ', attribute_data)
        print('  - Full data: ', binascii.hexlify(msg_data))

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
