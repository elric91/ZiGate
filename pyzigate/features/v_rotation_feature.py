import logging
from binascii import hexlify

from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0012'

    def get_name(self):
        return 'Rotation horizontal'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        if attr_id == b'0055':
            if hexlify(data) == b'0000':
                ZGT_LOG.info('  * Shaking')
            elif hexlify(data) == b'0055':
                ZGT_LOG.info('  * Rotating vertical')
                ZGT_LOG.info('  * Rotated: {}°'.format(int(hexlify(data), 16)))
            elif hexlify(data) == b'0103':
                ZGT_LOG.info('  * Sliding')
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Vertical Rotation commands sending.
    """
