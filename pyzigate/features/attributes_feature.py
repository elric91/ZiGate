import logging
import time
from collections import OrderedDict

from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0000'

    def get_name(self):
        return 'Attributes Parsing'

    def decode_msg(self, zigate, msg_type, msg_data):
        if msg_type == b'8140':
            struct = OrderedDict([('complete', 8), ('attr_type', 8), ('attr_id', 16)])
            msg = zigate.decode_struct(struct, msg_data)

            ZGT_LOG.debug('RESPONSE 8140 : Attribute Discovery indication')
            ZGT_LOG.debug('  - Attribute ID    : {}'.format(msg['attr_id']))
            ZGT_LOG.debug('  - Attribute Type  : {}'.format(msg['attr_type']))
            ZGT_LOG.debug('  - Discover Request Complete  : {} - {}'.format('Continue' if msg['complete'] == 0 else 'Last', msg['complete']))
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Attributes command sending.
    """

    def read_attribute(self, device_address, cluster_id, attribute_id, device_endpoint='01'):
        """
        Sends read attribute command to device

        :type self: Zigate
        :param str device_address: length 4. Example "AB01"
        :param str device_endpoint: length 2. Example "01"
        :param str cluster_id: length 4. Example "0000"
        :param str attribute_id: length 4. Example "0005"

        Examples:
        ========
        Replace device_address AB01 with your devices address.
        All clusters and parameters are not available on every device.
        - Get device manufacturer name: read_attribute('AB01', '01', '0000', '0004')
        - Get device name: read_attribute('AB01', '01', '0000', '0005')
        - Get device battery voltage: read_attribute('AB01', '01', '0001', '0006')
        """
        self.read_multiple_attributes(device_address, cluster_id, attribute_id, 1, device_endpoint)

    def read_multiple_attributes(self, device_address, cluster_id, first_attribute_id, attributes=16,
                                 device_endpoint='01'):
        """
        Constructs read_attribute command with multiple attributes and sends it

        :type self: Zigate
        :param str device_address: length 4. E
        :param str device_endpoint: length 2.
        :param str cluster_id: length 4.
        :param str first_attribute_id: length 4
        :param int attributes: How many attributes are requested. Max value 255

        Examples:
        ========
        Replace device_address AB01 with your devices address.
        All clusters and parameters are not available on every device.

        - Get five first attributes from "General: Basic" cluster:
          read_multiple_attributes('AB01', '01', '0000', '0000', 5)
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        cmd += cluster_id + ' 00 00 0000 ' + '{:02x}'.format(attributes)
        for i in range(attributes):
            cmd += ' ' + '{:04x}'.format(int(first_attribute_id, 16) + i)
        self.send_data('0100', cmd)

    def discover_attributes(self, device_address, cluster_id, attribute_id,
                            nb_attrs=255, manufacturer_id=None, device_endpoint='01'):
        """
        Attribute Discovery request

        :type self: Zigate
        :param str device_address: length 4. Example "AB01"
        :param cluster_id: length 4. Example "0000"
        :param attribute_id: length 4. Example "0005"
        :param nb_attrs: int Max: 255
        :param manufacturer_id: length 4. Example "AB01"
        :param str device_endpoint: length 2. Example "01"
        :return:
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        cmd += cluster_id + attribute_id
        cmd += ' 00 '
        cmd += '{:02x}'.format(0 if manufacturer_id is None else 1)
        cmd += ('0000' if manufacturer_id is None else manufacturer_id)
        cmd += '{:02x}'.format(nb_attrs)
        self.send_data('0140', cmd)

    def explore_attributes(self, device_address, cluster_id, size=32, device_endpoint='01'):
        for i in range(0, 65535, size):
            self.read_multiple_attributes(device_address, cluster_id,
                                          '{:04x}'.format(i), size, device_endpoint)
            time.sleep(2)
