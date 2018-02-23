import logging

from .abstract_feature import AbstractFeature

ZGT_LOG = logging.getLogger('zigate')


class Feature(AbstractFeature):
    def get_id(self):
        return b'000c'

    def get_name(self):
        return 'Rotation horizontal'


class CommandsMixin:
    """
    SubClass for the ZiGate class. Contains helper methods for Horizontal Rotation commands sending.
    """
