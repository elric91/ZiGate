#! /usr/bin/python3
import logging
from struct import unpack
from binascii import hexlify, unhexlify
from collections import OrderedDict
from time import strftime
from .zgt_parameters import *

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
        msg = self.decode_struct(struct, msg_data)
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
                raw_info = unhexlify(self.decode_struct(struct, attribute_data)['battery'])
                battery_info = int(hexlify(raw_info[::-1]), 16)/1000
                self.set_device_property(device_addr, endpoint, 'battery', battery_info)
                ZGT_LOG.info('  * Battery info')
                ZGT_LOG.info('  * Value : {} V'.format(battery_info))
        # Button status
        elif cluster_id == b'0006':
            ZGT_LOG.info('  * General: On/Off')
            if attribute_id == b'0000':
                if hexlify(attribute_data) == b'00':
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_ON)
                    ZGT_LOG.info('  * Closed/Taken off/Press')
                else:
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_OFF)
                    ZGT_LOG.info('  * Open/Release button')
            elif attribute_id == b'8000':
                clicks = int(hexlify(attribute_data), 16)
                self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_MULTI.format(clicks))
                ZGT_LOG.info('  * Multi click')
                ZGT_LOG.info('  * Pressed: {} times'.format(clicks))
        # Movement
        elif cluster_id == b'000c':  # Unknown cluster id
            if attribute_id == b'ff05':
                if hexlify(attribute_data) == b'01f4':
                    ZGT_LOG.info('  * Rotation horizontal')
            elif attribute_id == b'0055':
                ZGT_LOG.info('  * Rotated: %s°' % (unpack('!f', attribute_data)[0]))
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if hexlify(attribute_data) == b'0000':
                    ZGT_LOG.info('  * Shaking')
                elif hexlify(attribute_data) in [b'0100', b'0101', b'0102', b'0103', b'0104', b'0105']:
                    ZGT_LOG.info('  * Sliding')
                else:
                    ZGT_LOG.info('  * Rotating vertical')
                    if hexlify(attribute_data) in [b'0050', b'0042',
                                                   b'0044', b'0060',
                                                   b'0045', b'0068',
                                                   b'0041', b'0048',

                                                   b'0063', b'005c',
                                                   b'0059', b'004b',
                                                   b'005d', b'006b',
                                                   b'005a', b'0053',

                                                   b'004a', b'0051',
                                                   b'0054', b'0062',
                                                   b'0069', b'004d',
                                                   b'006c', b'0065',]:
                        ZGT_LOG.info('  * Rotated: 90°')
                    if hexlify(attribute_data) in [b'0080', b'0083',
                                                   b'0081', b'0084',
                                                   b'0085', b'0082',]:
                        ZGT_LOG.info('  * Rotated: 180°')
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
