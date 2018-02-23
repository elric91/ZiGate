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

        # Atmospheric Pressure
        if cluster_id == b'0403':
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
