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
