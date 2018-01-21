#! /usr/bin/python3
import logging
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
            ZGT_LOG.info('  * Rotation horizontal')
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if hexlify(attribute_data) == b'0000':
                    ZGT_LOG.info('  * Shaking')
                elif hexlify(attribute_data) == b'0055':
                    ZGT_LOG.info('  * Rotating vertical')
                    ZGT_LOG.info('  * Rotated: {}°'. format(int(hexlify(attribute_data), 16)))
                elif hexlify(attribute_data) == b'0103':
                    ZGT_LOG.info('  * Sliding')
        # Temperature
        elif cluster_id == b'0402':
            temperature = int(hexlify(attribute_data), 16) / 100
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
