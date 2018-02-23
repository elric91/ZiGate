import logging

from ..zgt_parameters import ZGT_ILLUMINANCE_MEASUREMENT
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0400'

    def get_name(self):
        return 'Measurement: Illuminance'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        # MeasuredValue
        if attr_id == b'0000':
            illuminance = int.from_bytes(data, 'big', signed=True)
            zigate.set_device_property(device_addr, endpoint, ZGT_ILLUMINANCE_MEASUREMENT, illuminance)
            return True

        # MinMeasuredValue
        if attr_id == b'0001':
            if data == b'FFFF':
                ZGT_LOG.info('Minimum illuminance is unused.')
            else:
                illuminance = int.from_bytes(data, 'big', signed=True)
                ZGT_LOG.info('Minimum illuminance is ', illuminance)
            return True

        # MaxMeasuredValue
        if attr_id == b'0002':
            if data == b'FFFF':
                ZGT_LOG.info('Maximum illuminance is unused.')
            else:
                illuminance = int.from_bytes(data, 'big', signed=True)
                ZGT_LOG.info('Maximum illuminance is ', illuminance)
            return True

        # Tolerance
        if attr_id == b'0003':
            illuminance = int.from_bytes(data, 'big', signed=True)
            ZGT_LOG.info('Illuminance tolerance is ', illuminance)
            return True

        # Sensor type
        if attr_id == b'0004':
            sensor_type = 'Unknown'
            if data == b'00':
                sensor_type = 'Photodiode'
            elif data == b'01':
                sensor_type = 'CMOS'
            elif b'02' <= data <= b'3F':
                sensor_type = 'Reserved'
            elif b'40' <= data <= b'FE':
                sensor_type = 'Reserved for manufacturer'
            ZGT_LOG.info('Sensor type is: ', sensor_type)
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Illuminance commands sending.
    """
