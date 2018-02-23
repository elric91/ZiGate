import logging
from binascii import hexlify
from .abstract_feature import AbstractFeature
from ..states import OnOffState
from ..zgt_parameters import *

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0006'

    def get_name(self):
        return 'General: On/Off'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        if attr_id == b'0000':
            if hexlify(data) == b'00':
                zigate.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_ON)
                ZGT_LOG.debug('  * Closed/Taken off/Press')
            else:
                zigate.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_OFF)
                ZGT_LOG.debug('  * Open/Release button')
            return True

        if attr_id == b'8000':
            clicks = int(hexlify(data), 16)
            zigate.set_device_property(device_addr, endpoint, ZGT_STATE, ZGT_STATE_MULTI.format(clicks))
            ZGT_LOG.debug('  * Multi click')
            ZGT_LOG.debug('  * Pressed: {} times'.format(clicks))
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for on/off command sending.
    """
    def switch(self, device_address, state, device_endpoint='01'):
        """
        Switch with no effects

        :type self: Zigate
        :param str device_address: length 4
        :param state: OnOffState
        :param str device_endpoint: length 2, default to '01'
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint + ('{:02x}'.format(state))
        self.send_data('0092', cmd)

    def off(self, device_address, device_endpoint='01'):
        """
        Off with no effects

        :type self: Zigate
        :param str device_address: length 4
        :param str device_endpoint: length 2, default to '01'
        """
        self.switch(device_address, OnOffState.OFF, device_endpoint)

    def on(self, device_address, device_endpoint='01'):
        """
        On with no effects

        :type self: Zigate
        :param str device_address: length 4
        :param str device_endpoint: length 2, default to '01'
        """
        self.switch(device_address, OnOffState.ON, device_endpoint)

    def toggle(self, device_address, device_endpoint='01'):
        """
        Toggle with no effects

        :type self: Zigate
        :param str device_address: length 4
        :param str device_endpoint: length 2, default to '01'
        """
        self.switch(device_address, OnOffState.SWITCH, device_endpoint)

