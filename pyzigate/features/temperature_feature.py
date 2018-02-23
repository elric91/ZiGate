import logging

from ..zgt_parameters import ZGT_TEMPERATURE
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0402'

    def get_name(self):
        return 'Measurement: Temperature'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        temperature = int.from_bytes(data, 'big', signed=True) / 100
        zigate.set_device_property(device_addr, endpoint, ZGT_TEMPERATURE, temperature)
        ZGT_LOG.info('  * Measurement: Temperature'),
        ZGT_LOG.info('  * Value: {} °C'.format(temperature))
        return True


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Horizontal Rotation commands sending.
    """
