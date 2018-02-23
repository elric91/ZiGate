import logging
from binascii import hexlify

from ..zgt_parameters import *
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0403'

    def get_name(self):
        return 'Measurement: Temperature'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        pressure = int(hexlify(data), 16)
        if attr_id == b'0000':
            zigate.set_device_property(device_addr, endpoint, ZGT_PRESSURE, pressure)
            ZGT_LOG.info('  * Value: {} mb'.format(pressure))
        elif attr_id == b'0010':
            zigate.set_device_property(device_addr, endpoint, ZGT_DETAILED_PRESSURE, pressure/10)
            ZGT_LOG.info('  * Value: {} mb'.format(pressure/10))
        elif attr_id == b'0014':
            ZGT_LOG.info('  * Value unknown')

        return True


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Atmospheric Pressure commands sending.
    """
