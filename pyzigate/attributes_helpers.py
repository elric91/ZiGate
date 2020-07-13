#! /usr/bin/python3
import logging
from struct import unpack
from binascii import hexlify, unhexlify
from collections import OrderedDict
from time import strftime
from .parameters import *
from .conversions import zgt_decode_struct

ZGT_LOG = logging.getLogger('zigate')

class Mixin:
    """
    SubClass for the ZiGate class. Contains methods for attribute handling
    """
    def interpret_attributes(self, msg_data):
        """
        Parses Zigbee message types 8100, 8102, 8110.
        Currently supports Xiaomi sensors and some of standardized clusters and attributes.

        :type self: Zigate
        :param msg_data: data from Zigbee message
        """
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
        msg = zgt_decode_struct(struct, msg_data)
        device_addr = msg['short_addr']
        endpoint = msg['endpoint']
        cluster_id = msg['cluster_id']
        attribute_id = msg['attribute_id']
        attribute_size = msg['attribute_size']
        attribute_data = msg['attribute_data']
        self.set_device_property(device_addr, endpoint, ZGT_LAST_SEEN, strftime('%Y-%m-%d %H:%M:%S'))

        if msg['sequence'] == b'00':
            ZGT_LOG.debug('  - Sensor type announce (Start after pairing 1)')
        elif msg['sequence'] == b'01':
            ZGT_LOG.debug('  - Something announce (Start after pairing 2)')

        # Device type
        if cluster_id == b'0000':
            if attribute_id == b'0005':
                self.set_device_property(device_addr, endpoint, 'type', attribute_data.decode())
                ZGT_LOG.info(' * type : {}'.format(attribute_data))
            ## proprietary Xiaomi info including battery
            if attribute_id == b'ff01' and attribute_data != b'':
                struct = OrderedDict([('start', 16), ('battery', 16), ('end', 'rawend')])
                raw_info = unhexlify(zgt_decode_struct(struct, attribute_data)['battery'])
                battery_info = int(hexlify(raw_info[::-1]), 16)/1000
                self.set_device_property(device_addr, endpoint, 'battery', battery_info)
                ZGT_LOG.info('  * Battery info')
                ZGT_LOG.info('  * Value : {} V'.format(battery_info))
        # Button status
        elif cluster_id == b'0006':
            ZGT_LOG.info('  * General: On/Off')
            if attribute_id == b'0000':
                if hexlify(attribute_data) == b'00':
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_OFF)
                    ZGT_LOG.info('  * Closed/Taken off/Press')
                else:
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_ON)
                    ZGT_LOG.info('  * Open/Release button')
            elif attribute_id == b'8000':
                clicks = int(hexlify(attribute_data), 16)
                self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_MULTI.format(clicks))
                ZGT_LOG.info('  * Multi click')
                ZGT_LOG.info('  * Pressed: {} times'.format(clicks))
        # Movement
        elif cluster_id == b'000c':  # Unknown cluster id
            if attribute_id == b'ff05':
                ZGT_LOG.info('  * Horizontal Rotation Announce with value {}'.format(hexlify(attribute_data)))
            elif attribute_id == b'0055':
                ZGT_LOG.info('  * Horizontal Rotation Value: %s°' % (unpack('!f', attribute_data)[0]))
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if hexlify(attribute_data) == b'0000':
                    ZGT_LOG.info('  * Shaking')
                elif attribute_data[0] == 1: # b'01xx'
                    ZGT_LOG.info('  * Sliding on face {}'.format(attribute_data[1]))
                elif attribute_data[0] == 0: # b'00xx' with xx != 00
                    # binary format
                    # aa : 01 = 90° 10 = 180°
                    # bbb : face (from) number (if 180° always 000)
                    # ccc : face (to) number
                    rotation_info = [(attribute_data[1] >> i) & 1 for i in range(7, -1, -1)]
                    rotation_info = ''.join([str(x) for x in rotation_info])
                    rotation_type = int(rotation_info[0:2],2)
                    rotation_from = int(rotation_info[2:5],2)
                    rotation_to = int(rotation_info[5:8],2)
                    if rotation_type == 2:
                        ZGT_LOG.info('  * 180° Rotation to face {}'.format(rotation_to))
                    else:
                        ZGT_LOG.info('  * 90° Rotation from face {} to face {}'.format(rotation_from, rotation_to))
                        
        # Illuminance Measurement
        elif cluster_id == b'0400':
            # MeasuredValue
            if attribute_id == b'0000':
                illuminance = int.from_bytes(attribute_data, 'big', signed=True)
                self.set_device_property(device_addr, endpoint, ZGT_ILLUMINANCE_MEASUREMENT, illuminance)
            # MinMeasuredValue
            elif attribute_id == b'0001':
                if attribute_data == b'FFFF':
                    ZGT_LOG.info('Minimum illuminance is unused.')
                else:
                    illuminance = int.from_bytes(attribute_data, 'big', signed=True)
                    ZGT_LOG.info('Minimum illuminance is ', illuminance)
            # MaxMeasuredValue
            elif attribute_id == b'0002':
                if attribute_data == b'FFFF':
                    ZGT_LOG.info('Maximum illuminance is unused.')
                else:
                    illuminance = int.from_bytes(attribute_data, 'big', signed=True)
                    ZGT_LOG.info('Maximum illuminance is ', illuminance)
            # Tolerance
            elif attribute_id == b'0003':
                illuminance = int.from_bytes(attribute_data, 'big', signed=True)
                ZGT_LOG.info('Illuminance tolerance is ', illuminance)
            # Sensor type
            elif attribute_id == b'0004':
                sensor_type = 'Unknown'
                if attribute_data == b'00':
                    sensor_type = 'Photodiode'
                elif attribute_data == b'01':
                    sensor_type = 'CMOS'
                elif b'02' <= attribute_data <= b'3F':
                    sensor_type = 'Reserved'
                elif b'40' <= attribute_data <= b'FE':
                    sensor_type = 'Reserved for manufacturer'
                ZGT_LOG.info('Sensor type is: ', sensor_type)
        # Temperature
        elif cluster_id == b'0402':
            temperature = int.from_bytes(attribute_data, 'big', signed=True) / 100
            #temperature = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, endpoint, ZGT_TEMPERATURE, temperature)
            ZGT_LOG.info('  * Measurement: Temperature'),
            ZGT_LOG.info('  * Value: {} °C'.format(temperature))
        # Atmospheric Pressure
        elif cluster_id == b'0403':
            ZGT_LOG.info('  * Atmospheric pressure')
            pressure = int(hexlify(attribute_data), 16)
            if attribute_id == b'0000':
                self.set_device_property(device_addr, endpoint, ZGT_PRESSURE, pressure)
                ZGT_LOG.info('  * Value: {} mb'.format(pressure))
            elif attribute_id == b'0010':
                self.set_device_property(device_addr, endpoint, ZGT_DETAILED_PRESSURE, pressure/10)
                ZGT_LOG.info('  * Value: {} mb'.format(pressure/10))
            elif attribute_id == b'0014':
                ZGT_LOG.info('  * Value unknown')
        # Humidity
        elif cluster_id == b'0405':
            humidity = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, endpoint, ZGT_HUMIDITY, humidity)
            ZGT_LOG.info('  * Measurement: Humidity')
            ZGT_LOG.info('  * Value: {} %'.format(humidity))
        # Presence Detection
        elif cluster_id == b'0406':
            # Only sent when movement is detected
            if hexlify(attribute_data) == b'01':
                self.set_device_property(device_addr, endpoint, ZGT_EVENT, ZGT_EVENT_PRESENCE)
                ZGT_LOG.debug('   * Presence detection')

        ZGT_LOG.info('  FROM ADDRESS      : {}'.format(msg['short_addr']))
        ZGT_LOG.debug('  - Source EndPoint : {}'.format(msg['endpoint']))
        ZGT_LOG.debug('  - Cluster ID      : {}'.format(msg['cluster_id']))
        ZGT_LOG.debug('  - Attribute ID    : {}'.format(msg['attribute_id']))
        ZGT_LOG.debug('  - Attribute type  : {}'.format(msg['attribute_type']))
        ZGT_LOG.debug('  - Attribute size  : {}'.format(msg['attribute_size']))
        ZGT_LOG.debug('  - Attribute data  : {}'.format(hexlify(msg['attribute_data'])))
