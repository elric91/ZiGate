#! /usr/bin/python3
import serial
import threading
import binascii
from time import (sleep, strftime)

class ZiGate():

    def __init__(self, device="/dev/ttyUSB0"):
        self.conn = serial.Serial(device, 115200, timeout=0)
        self.buffer = b''
        self.thread = threading.Thread(target=self.read_data).start()
        self.devices = []

    def stop(self):
        self.conn.close()


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

    def read_data(self):
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
                    self.interpret(data_to_decode)  # stripping starting 0x01 & ending 0x03
                    self.buffer = self.buffer[endpos + 1:]

    def send_data(self, cmd, data=""):

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

    def interpret(self, data):

        msg_data = data[6:]
        # Do different things based on MsgType
        # Device Announce
        if binascii.hexlify(data[:2]) == b'004d':
            print('  - This is Device Announce')
            print('    * From address: ', binascii.hexlify(msg_data[:2]))
            print('    * MAC address: ', binascii.hexlify(msg_data[2:10]))
            print('    * MAC capability: ', binascii.hexlify(msg_data[10:11]))
            print('    * Full data: ', binascii.hexlify(msg_data))
        # Status
        elif binascii.hexlify(data[:2]) == b'8000':
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
            print('  - This is Status [%s]' % status_text)
            print('    * Sequence: ', binascii.hexlify(data[6:7]))
            print('    * Response to command: ', binascii.hexlify(data[7:9]))
            if binascii.hexlify(data[9:]) != b'00':
                print('  *Additional msg: ', binascii.hexlify(data[9:]))  # Bin to Hex
        # Default Response
        elif binascii.hexlify(data[:2]) == b'8001':
            print(' - This is Default Response')
            print('   * After decoding : ', binascii.hexlify(data))
        # Version list
        elif binascii.hexlify(data[:2]) == b'8010':
            print(' - This is version list')
            print('   * Major version : ', binascii.hexlify(data[6:8]))
            print('   * Installer version : ', binascii.hexlify(data[8:10]))
        # Attribute Report
        # Currently only support Xiaomi sensors. Other brands might calc things differently
        elif binascii.hexlify(data[:2]) == b'8102':
            self.interpret_xiaomi(data, msg_data)
        # Route Discovery Confirmation
        elif binascii.hexlify(data[:2]) == b'8701':
            sequence = binascii.hexlify(data[5:6])
            print(' - This is Route Discovery Confirmation')
            print('   * Sequence: ', sequence)
            print('   * Status: ', binascii.hexlify(msg_data[0:1]))
            print('   * Network status: ', binascii.hexlify(msg_data[1:2]))
            print('   * Full data: ', binascii.hexlify(msg_data))
        # No handling for this type of message
        else:
            print(' - Unknown message')
            print('   * After decoding : ', binascii.hexlify(data))
            print('   * MsgType		: ', binascii.hexlify(data[:2]))
            print('   * MsgLength	: ', binascii.hexlify(data[2:4]))
            print('   * RSSI		: ', binascii.hexlify(data[4:5]))
            print('   * ChkSum		: ', binascii.hexlify(data[5:6]))
            print('   * Data		: ', binascii.hexlify(data[6:]))

    def interpret_xiaomi(self, ddata, msg_data):
        self.sequence = binascii.hexlify(ddata[5:6])
        attribute_size = int(binascii.hexlify(msg_data[9:11]), 16)  # Convert attribute size data to int
        attribute_data = binascii.hexlify(msg_data[11:11 + attribute_size])
        attribute_id = binascii.hexlify(msg_data[5:7])
        cluster_id = binascii.hexlify(msg_data[3:5])
        print('  - This is Attribute Report')
        if self.sequence == b'00':
            print('    * Sensor type announce (Start after pairing 1)')
        elif self.sequence == b'01':
            print('    * Something announce (Start after pairing 2)')
        # Which attribute
        if cluster_id == b'0006':
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
            print('    * Measurement: Temperature'),
            print('    * Value: ', int(attribute_data, 16) / 100, "°C")
        elif cluster_id == b'0403':
            print('    * Atmospheric pressure')
            if attribute_id in (b'0000', b'0010'):
                print('    * Value: ', int(attribute_data, 16), "mb")
            elif attribute_id == b'0014':
                print('    * Value unknown')
        elif cluster_id == b'0405':
            print('    * Measurement: Humidity')
            print('    * Value: ', int(attribute_data, 16) / 100, "%")
        elif cluster_id == b'0406':
            print('   * Presence detection')  # Only sent when movement is detected

        print('  - From address: ', binascii.hexlify(msg_data[:2]))
        print('  - Source Ep: ', binascii.hexlify(msg_data[2:3]))
        print('  - Cluster ID: ', cluster_id)
        print('  - Attribute ID: ', attribute_id)
        print('  - Attribute size: ', binascii.hexlify(msg_data[9:11]))
        print('  - Attribute type: ', binascii.hexlify(msg_data[8:9]))
        print('  - Attribute data: ', binascii.hexlify(msg_data[11:11 + attribute_size]))
        print('  - Full data: ', binascii.hexlify(msg_data))



    def list_devices(self):
        for dev in self.devices:
            print("ID: %s - type %s" % (dev.address, dev.type))


    def zigate(self, subcmd):
        if subcmd[0] == 'reset':
            self.send_data("0011")  # Zigate chip reset 
        elif subcmd[0] == 'version':  
            self.send_data("0010")

    def network(self, subcmd):
        if subcmd[0] == 'reset':
            self.send_data("0024")
        elif subcmd[0] == 'scan':  
            self.send_data("0025")
        elif subcmd[0] == 'permit_join':  
            self.send_data("0014")
        elif subcmd[0] == 'restart':
            self.send_data("0021", "00000800")  # Set Channel to mask
            self.send_data("0023")  # Set Device Type [Coordinator]
            self.send_data("0024")  # Start Network
            # self.send_data("0049", "FFFCFE00")


class endpoint():
    
    def __init__(self, short_address):
      self._address = short_address
      self._type = 'unknown'

    @property
    def type(self):
        return self._type

    @property
    def address(self):
        return self._address



commands = {'help':'This help', 
            'exit':'Quit', 
            'quit':'Same as exit', 
            'zigate':'reset / version',
            'network':'reset / scan / permit_join / full_reset',
           }

if __name__ == "__main__":
    zigate = ZiGate()
    while True:
        cmd = input('>').strip().split(' ')
         
        if cmd[0] in ('exit', 'quit'):
            print('exiting ...')
            zigate.stop()
            raise SystemExit
        elif cmd[0] == 'help':
           for c in commands.keys():
               print('%s : %s' % (c, commands[c]))
        elif cmd[0] in commands.keys():
            func = getattr(zigate, cmd[0])
            func(cmd[1:])
        else:
            print("Command '%s' unkown !" % ' '.join(cmd))
        sleep(1)
