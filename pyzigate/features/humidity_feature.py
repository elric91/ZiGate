import logging
from binascii import hexlify

from ..zgt_parameters import ZGT_HUMIDITY
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0405'

    def get_name(self):
        return 'Measurement: Humidity'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        humidity = int(hexlify(data), 16) / 100
        zigate.set_device_property(device_addr, endpoint, ZGT_HUMIDITY, humidity)
        ZGT_LOG.info('  * Measurement: Humidity')
        ZGT_LOG.info('  * Value: {} %'.format(humidity))
        return True


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Humidity commands sending.
    """
