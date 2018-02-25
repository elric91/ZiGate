import logging

from ..zgt_parameters import ZGT_LEVEL, ZGT_LEVEL_MAX, ZGT_LEVEL_PERCENT
from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'0008'

    def get_name(self):
        return 'General: Level Control'

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        if attr_id == b'0000':
            level = int.from_bytes(data, 'big', signed=False)
            zigate.set_device_property(device_addr, endpoint, ZGT_LEVEL, level)
            zigate.set_device_property(device_addr, endpoint, ZGT_LEVEL_PERCENT, (level/254)*100)
            ZGT_LOG.info('  * Current Level : {} - {}%'.format(level, (level/254)*100))
            return True

        if attr_id == b'0011':
            max_level = int.from_bytes(data, 'big', signed=False)
            zigate.set_device_property(device_addr, endpoint, ZGT_LEVEL_MAX, max_level)
            ZGT_LOG.info('  * Max Level : {}'.format(max_level))
            return True

        return False


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Level control commands sending.
    """
    def stop_move(self, device_address, with_on_off=True, device_endpoint='01'):
        """
        Stop current move

        :type self: Zigate
        :param str device_address: length 4
        :param bool with_on_off: Specifies whether this cluster interacts with the On/Off cluster
        :param str device_endpoint: length 2, default to '01'
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        self.send_data('0084' if with_on_off else '0083', cmd)

    def move(self, device_address, level, transition_time=0, with_on_off=True, device_endpoint='01'):
        """
        Move to level

        :type self: Zigate
        :param str device_address: length 4
        :param int level: 0 to 255
        :param int transition_time : is the time taken, in units of tenths of a second, to reach the target level
                                     (>= 65535 means move to the level as fast as possible)
        :param bool with_on_off: Specifies whether this cluster interacts with the On/Off cluster
        :param str device_endpoint: length 2, default to '01'
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        cmd += ('{:02x}'.format(1 if with_on_off else 0))
        cmd += ('{:02x}'.format(level))
        cmd += ('{:04x}'.format(max(transition_time, 65535)))
        self.send_data('0081', cmd)

    def move_relative(self, device_address, step_size, transition_time=0, with_on_off=True, device_endpoint='01'):
        """
        Relative Move

        :type self: Zigate
        :param str device_address: length 4
        :param int step_size: -255 to 0 to 255 (relative to current level); negative down, positive up
        :param int transition_time : is the time taken, in units of tenths of a second, to reach the target level
                                     (>= 65535 means move to the level as fast as possible)
        :param bool with_on_off: Specifies whether this cluster interacts with the On/Off cluster
        :param str device_endpoint: length 2, default to '01'
        """
        cmd = self.address_mode + device_address + self.src_endpoint + device_endpoint
        cmd += ('{:02x}'.format(1 if with_on_off else 0))
        cmd += ('{:02x}'.format(1 if step_size < 0 else 0))
        cmd += ('{:02x}'.format(abs(step_size)))
        cmd += ('{:04x}'.format(max(transition_time, 65535)))
        self.send_data('0082', cmd)
