#! /usr/bin/python3
import serial
import threading
import binascii


class ZiGate():

    def __init__(self, device="/dev/ttyUSB0"):
        self.conn = serial.Serial(device, 115200, timeout=0)
        self.buffer = b''
        threading.Thread(target=self.read_data).start()

    def read_data(self):
        while (True):
            bytesavailable = self.conn.inWaiting()
            if (bytesavailable > 0):
                self.buffer += self.conn.read(bytesavailable)
                endpos = self.buffer.find(b'\x03')
                if endpos != -1:
                    startpos = self.buffer.find(b'\x01')
                    print('received data : ', binascii.hexlify(self.buffer[startpos:endpos + 1]))
                    self.decode(self.buffer[startpos + 1:endpos])  # stripping starting 0x01 & ending 0x03
                    self.buffer = self.buffer[endpos + 1:]

    def send_data(self, cmd, length, data):

        bcmd = bytes.fromhex(cmd)
        blength = bytes.fromhex(length)
        bdata = bytes.fromhex(data)

        msg = [0x01]
        msg.extend(self.transcode(bcmd))
        msg.extend(self.transcode(blength))

        msg.append(self.checksum(bcmd, blength, bdata))

        if data != "":
            msg.extend(self.transcode(bdata))

        msg.append(0x03)

        sdata = b''.join([bytes([x]) for x in msg])
        print('Send data : ', binascii.hexlify(sdata))
        self.conn.write(sdata)

    def decode(self, data):
        transcoded = False
        ddata = b''
        for x in data:
            if bytes([x]) == b'\x02':
                transcoded = True
            elif transcoded == True:
                transcoded = False
                ddata += self.bxor_join(bytes([x]), b'\x10')
            else:
                ddata += bytes([x])
        msg_data = ddata[6:]
        # Do different things based on MsgType
        # Device Announce
        if binascii.hexlify(ddata[:2]) == b'004d':
            print('This is Device Announce')
            print('From address: ', binascii.hexlify(msg_data[:2]))
            print('MAC address: ', binascii.hexlify(msg_data[2:10]))
            print('MAC capability: ', binascii.hexlify(msg_data[10:11]))
            print('Full data: ', binascii.hexlify(msg_data))
        # Status
        elif binascii.hexlify(ddata[:2]) == b'8000':
            status_code = int(binascii.hexlify(ddata[5:6]), 16)
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
            print('This is Status [%s]' % status_text)
            print('Sequence: ', binascii.hexlify(ddata[6:7]))
            print('Response to command: ', binascii.hexlify(ddata[7:9]))
            if binascii.hexlify(ddata[9:]) != b'00':
                print('Additional msg: ', binascii.hexlify(ddata[9:]))  # Bin to Hex
        # Default Response
        elif binascii.hexlify(ddata[:2]) == b'8001':
            print('This is Default Response')
            print('After decoding : ', binascii.hexlify(ddata))
        # Version list
        elif binascii.hexlify(ddata[:2]) == b'8010':
            print('This is version list')
            print('Major version : ', binascii.hexlify(ddata[6:8]))
            print('Installer version : ', binascii.hexlify(ddata[8:10]))
        # Attribute Report
        # Currently only support Xiaomi sensors. Other brands might calc things differently
        elif binascii.hexlify(ddata[:2]) == b'8102':
            self.interpret_xiaomi(ddata, msg_data)
        # Route Discovery Confirmation
        elif binascii.hexlify(ddata[:2]) == b'8701':
            sequence = binascii.hexlify(ddata[5:6])
            print('This is Route Discovery Confirmation')
            print('Sequence: ', sequence)
            print('Status: ', binascii.hexlify(msg_data[0:1]))
            print('Network status: ', binascii.hexlify(msg_data[1:2]))
            print('Full data: ', binascii.hexlify(msg_data))
        # No handling for this type of message
        else:
            print('Unknown message')
            print('After decoding : ', binascii.hexlify(ddata))
            print('MsgType		: ', binascii.hexlify(ddata[:2]))
            print('MsgLength	: ', binascii.hexlify(ddata[2:4]))
            print('RSSI		: ', binascii.hexlify(ddata[4:5]))
            print('ChkSum		: ', binascii.hexlify(ddata[5:6]))
            print('Data		: ', binascii.hexlify(ddata[6:]))

    def interpret_xiaomi(self, ddata, msg_data):
        self.sequence = binascii.hexlify(ddata[5:6])
        attribute_size = int(binascii.hexlify(msg_data[9:11]), 16)  # Convert attribute size data to int
        attribute_data = binascii.hexlify(msg_data[11:11 + attribute_size])
        attribute_id = binascii.hexlify(msg_data[5:7])
        cluster_id = binascii.hexlify(msg_data[3:5])
        print('This is Attribute Report')
        if sequence == b'00':
            print('Sensor type announce (Start after pairing 1)')
        elif sequence == b'01':
            print('Something announce (Start after pairing 2)')
        # Which attribute
        if cluster_id == b'0006':
            print('General: On/Off')
            if attribute_id == b'0000':
                if attribute_data == b'00':
                    print('Closed/Taken off/Press')
                else:
                    print('Open/Release button')
            elif attribute_id == b'8000':
                print('Multi click')
                print('Pressed: ', int(attribute_data, 16), " times")
        elif cluster_id == b'000c':  # Unknown cluster id
            print('Rotation horizontal')
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if attribute_data == b'0000':
                    print('Shaking')
                elif attribute_data == b'0055':
                    print('Rotating vertical')
                    print('Rotated: ', int(attribute_data, 16), "°")
                elif attribute_data == b'0103':
                    print('Sliding')
        elif cluster_id == b'0402':
            print('Measurement: Temperature'),
            print('Value: ', int(attribute_data, 16) / 100, "°C")
        elif cluster_id == b'0403':
            print('Atmospheric pressure')
            if attribute_id in (b'0000', b'0010'):
                print('Value: ', int(attribute_data, 16), "mb")
            elif attribute_id == b'0014':
                print('Value unknown')
        elif cluster_id == b'0405':
            print('Measurement: Humidity')
            print('Value: ', int(attribute_data, 16) / 100, "%")
        elif cluster_id == b'0406':
            print('Presence detection')  # Only sent when movement is detected

        print('From address: ', binascii.hexlify(msg_data[:2]))
        print('Source Ep: ', binascii.hexlify(msg_data[2:3]))
        print('Cluster ID: ', cluster_id)
        print('Attribute ID: ', attribute_id)
        print('Attribute size: ', binascii.hexlify(msg_data[9:11]))
        print('Attribute type: ', binascii.hexlify(msg_data[8:9]))
        print('Attribute data: ', binascii.hexlify(msg_data[11:11 + attribute_size]))
        print('Full data: ', binascii.hexlify(msg_data))



    @staticmethod
    def bxor_join(b1, b2):  # use xor for bytes
        parts = []
        for b1, b2 in zip(b1, b2):
            parts.append(bytes([b1 ^ b2]))
        return b''.join(parts)

    @staticmethod
    def transcode(data):
        transcoded = []
        for x in data:
            if x < 0x10:
                transcoded.append(0x02)
                transcoded.append(x ^ 0x10)
            else:
                transcoded.append(x)

        return transcoded

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

    def reset(self):
        self.send_data("0021", "0004", "00000800")  # Set Channel Mask
        self.send_data("0023", "0001", "00")  # Set Device Type [Router]
        self.send_data("0024", "0000", "")  # Start Network
        self.send_data("0049", "0004", "FFFCFE00")

if __name__ == "__main__":
    zigate = ZiGate()
    zigate.send_data("0010", "0000", "")
    zigate.reset()

