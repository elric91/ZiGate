import logging
from binascii import hexlify

from ..zgt_parameters import *
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0406'

    def get_name(self):
        return 'Measurement: Occupancy Sensing'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        # Only sent when movement is detected
        if hexlify(data) == b'01':
            zigate.set_device_property(device_addr, endpoint, ZGT_EVENT, ZGT_EVENT_PRESENCE)
            ZGT_LOG.debug('   * Presence detection')
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Occupancy Sensing commands sending.
    """
