#! /usr/bin/python3
import logging
from binascii import hexlify
from collections import OrderedDict
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

        # Illuminance Measurement
        if cluster_id == b'0400':
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
