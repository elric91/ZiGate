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
					print('received data : ', binascii.hexlify(self.buffer[startpos:endpos+1]))
					self.decode(self.buffer[startpos+1:endpos]) # stripping starting 0x01 & ending 0x03
					self.buffer = self.buffer[endpos+1:]

	def send_data(self, cmd, length, data):
		
		bcmd = bytes.fromhex(cmd)
		blength = bytes.fromhex(length)
		bdata = bytes.fromhex(data)

		msg = [0x01]
		msg.extend(self.transcode(bcmd))
		msg.extend(self.transcode(blength))

		msg.append(self.checksum(bcmd, blength, bdata))

		if data != "" :
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
		# Attribute Report
		# Currentyly only support Xiaomi sensors. Other brands might calc things differently
		elif binascii.hexlify(ddata[:2]) == b'8102':
			sequence = binascii.hexlify(ddata[5:6])
			attribute_size = int(binascii.hexlify(msg_data[9:11]), 16)  # Convert attribute size data to int
			attribute_data = binascii.hexlify(msg_data[11:11+attribute_size])
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
				if attribute_data == b'00':
					print('Closedi/Taken off')
				else:
					print('Open')
			elif cluster_id == b'0406':
				print('Presence detection')  # Only sent when movement is detected
			elif cluster_id == b'0402':
				print('Measurement: Temperature'),
				print('Value: ', int(attribute_data, 16) / 100, "°C")
			elif cluster_id == b'0405':
				print('Measurement: Humidity')
				print('Value: ', int(attribute_data, 16) / 100, "%")
			elif cluster_id == b'0403':
				print('Atmospheric pressure')
				if attribute_id in (b'0000', b'0010'):
					print('Value: ', int(attribute_data, 16), "mb")
				elif attribute_id == b'0014':
					print('Value unknown')
			elif cluster_id == b'0012':
				if attribute_id == b'0055':
					if attribute_data == b'0000':
						print('Shaking')
					elif attribute_data == b'0103':
						print('Sliding')
				
			print('From address: ', binascii.hexlify(msg_data[:2]))
			print('Source Ep: ', binascii.hexlify(msg_data[2:3]))
			print('Cluster ID: ', cluster_id)
			print('Attribute ID: ', attribute_id)
			print('Attribute size: ', binascii.hexlify(msg_data[9:11]))
			print('Attribute type: ', binascii.hexlify(msg_data[8:9]))
			print('Attribute data: ', binascii.hexlify(msg_data[11:11+attribute_size]))
			print('Full data: ', binascii.hexlify(msg_data))
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

#	def interpret(self, msg_type, data):
#		output = []
#
#		if msg_type == "8000":
#			txt_status = ("Success", "Incorrect parameters", "Unhandled command", "Command failed", "Busy (Node is carrying out a lengthy operation and is currently unable to handle the incoming command)", "Stack already started (no new configuration accepted)", "Failed (ZigBee event codes)", "Unknown")
#			if data[0] < 6:
#				output.append("Status : %s" % txt_status[data[0]])
#			elif data[0] >=128 and data[0] <=244:
#				output.append("Status : %s - code %s" % (txt_status[-2], data[0]))
#			else:
#				output.append("Status : %s - code %s" % (txt_status[-1], data[0]))
#			output.append("	


	def bxor_join(self, b1, b2): # use xor for bytes
		parts = []
		for b1, b2 in zip(b1, b2):
			parts.append(bytes([b1 ^ b2]))
		return b''.join(parts)


	def transcode(self, data):
		transcoded = []
		for x in data:
			if x < 0x10:
				transcoded.append(0x02)
				transcoded.append(x ^ 0x10)
			else:
				transcoded.append(x)

		return transcoded

	def checksum(self, cmd, length, data):
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
		self.send_data("0021", "0004", "00000800")
		self.send_data("0023", "0001", "00")
		self.send_data("0024", "0000", "")
		self.send_data("0049", "0004", "FFFCFE00")


zigate = ZiGate()
zigate.send_data("0010", "0000", "")
zigate.reset()
