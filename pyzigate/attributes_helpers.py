#! /usr/bin/python3
# coding: utf8
from binascii import hexlify
from collections import OrderedDict
from time import strftime
from .zgt_parameters import *


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
            self._logger.debug('  - Sensor type announce (Start after pairing 1)')
        elif msg['sequence'] == b'01':
            self._logger.debug('  - Something announce (Start after pairing 2)')

        # Device type
        if cluster_id == b'0000':
            if attribute_id == b'0005':
                self.set_device_property(device_addr, endpoint, 'type', attribute_data.decode())
                self._logger.info(' * type : {}'.format(attribute_data))
        # Button status
        elif cluster_id == b'0006':
            self._logger.info('  * General: On/Off')
            if attribute_id == b'0000':
                if hexlify(attribute_data) == b'00':
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_ON)
                    self._logger.info('  * Closed/Taken off/Press')
                else:
                    self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_OFF)
                    self._logger.info('  * Open/Release button')
            elif attribute_id == b'8000':
                clicks = int(hexlify(attribute_data), 16)
                self.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_MULTI.format(clicks))
                self._logger.info('  * Multi click')
                self._logger.info('  * Pressed: {} times'.format(clicks))
        # Movement
        elif cluster_id == b'000c':  # Unknown cluster id
            self._logger.info('  * Rotation horizontal')
        elif cluster_id == b'0012':  # Unknown cluster id
            if attribute_id == b'0055':
                if hexlify(attribute_data) == b'0000':
                    self._logger.info('  * Shaking')
                elif hexlify(attribute_data) == b'0055':
                    self._logger.info('  * Rotating vertical')
                    self._logger.info('  * Rotated: {}°'. format(int(hexlify(attribute_data), 16)))
                elif hexlify(attribute_data) == b'0103':
                    self._logger.info('  * Sliding')
        # Temperature
        elif cluster_id == b'0402':
            temperature = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, endpoint, ZGT_TEMPERATURE, temperature)
            self._logger.info('  * Measurement: Temperature'),
            self._logger.info('  * Value: {}'.format(temperature, '°C'))
        # Atmospheric Pressure
        elif cluster_id == b'0403':
            self._logger.info('  * Atmospheric pressure')
            pressure = int(hexlify(attribute_data), 16)
            if attribute_id == b'0000':
                self.set_device_property(device_addr, endpoint, ZGT_PRESSURE, pressure)
                self._logger.info('  * Value: {}'.format(pressure, 'mb'))
            elif attribute_id == b'0010':
                self.set_device_property(device_addr, endpoint, ZGT_DETAILED_PRESSURE, pressure/10)
                self._logger.info('  * Value: {}'.format(pressure/10, 'mb'))
            elif attribute_id == b'0014':
                self._logger.info('  * Value unknown')
        # Humidity
        elif cluster_id == b'0405':
            humidity = int(hexlify(attribute_data), 16) / 100
            self.set_device_property(device_addr, endpoint, ZGT_HUMIDITY, humidity)
            self._logger.info('  * Measurement: Humidity')
            self._logger.info('  * Value: {}'.format(humidity, '%'))
        # Presence Detection
        elif cluster_id == b'0406':
            # Only sent when movement is detected
            if hexlify(attribute_data) == b'01':
                self.set_device_property(device_addr, endpoint, ZGT_EVENT, ZGT_EVENT_PRESENCE)
                self._logger.debug('   * Presence detection')

        self._logger.info('  FROM ADDRESS      : {}'.format(msg['short_addr']))
        self._logger.debug('  - Source EndPoint : {}'.format(msg['endpoint']))
        self._logger.debug('  - Cluster ID      : {}'.format(msg['cluster_id']))
        self._logger.debug('  - Attribute ID    : {}'.format(msg['attribute_id']))
        self._logger.debug('  - Attribute type  : {}'.format(msg['attribute_type']))
        self._logger.debug('  - Attribute size  : {}'.format(msg['attribute_size']))
        self._logger.debug('  - Attribute data  : {}'.format(hexlify(msg['attribute_data'])))
