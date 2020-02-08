#! /usr/bin/python3
import logging
from .parameters import * 
from collections import OrderedDict
from binascii import hexlify
from .conversions import zgt_decode_struct, zgt2int
from .attributes import ATTRIBUTES

ZGT_LOG = logging.getLogger('zigate')
RESPONSES = {}

def register_response(response):
    RESPONSES[response.id] = response
    return response


class Response(object):
    id = None
    descr = 'Unknown Message'
    struct = OrderedDict()
    
    def __init__(self, data):
        self.msg_type = zgt2int(data[0:2])
        self.msg_length = zgt2int(data[2:4])
        self.msg_crc = zgt2int(data[4:5])
        self.msg_data = data[5:]
        self.msg_rssi = zgt2int(data[-1:])
        
        self.msg = zgt_decode_struct(self.struct, self.msg_data)
        self.external_commands = OrderedDict()
        self.add_external_commands()

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        for key in self.msg:
            ZGT_LOG.debug('  - {:<20} : {}'.format(key, self.msg[key]))
    
    def add_external_commands(self):
        pass

    def get_external_commands(self):
        return self.external_commands


@register_response
class Response_004d(Response):
    id = 0x004d
    descr = 'Device Announce'
    struct = OrderedDict([('short_addr', 16), ('mac_addr', 64), ('mac_capability', 'rawend')])

    def add_external_command(self):
        self.external_commands[ZGT_CMD_NEW_DEVICE] = {'addr': self.msg['short_addr'].decode()}


@register_response
class Response_8000(Response):
    id = 0x8000
    descr = 'Status'
    struct = OrderedDict([('status', 'int'), ('sequence', 8),('packet_type', 16), ('info', 'rawend')])

    def __init__(self, data):
        super().__init__(data)
        status_codes = {0: 'Success', 1: 'Invalid parameters',
                        2: 'Unhandled command', 3: 'Command failed',
                        4: 'Busy', 5: 'Stack already started'}
        self.status_text = status_codes.get(self.msg['status'], 'Failed with event code: %i' % self.msg['status'])

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        ZGT_LOG.debug('  * Status              : {}'.format(self.status_text))
        ZGT_LOG.debug('  - Sequence            : {}'.format(self.msg['sequence']))
        ZGT_LOG.debug('  - Response to command : {}'.format(self.msg['packet_type']))
        if zgt2int(self.msg['info']) != 0x00:
            ZGT_LOG.debug('  - Additional msg: ', zgt2int(self.msg['info']))


@register_response
class Response_8001(Response):
    id = 0x8001
    descr = 'Default Response'
    struct = OrderedDict([('level', 'int'), ('info', 'rawend')])

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        zgt_log_levels = ['Emergency', 'Alert', 'Critical', 'Error',
                              'Warning', 'Notice', 'Information', 'Debug']

        ZGT_LOG.debug('  - Log Level : {}'.format(zgt_log_levels[msg['level']]))
        ZGT_LOG.debug('  - Log Info  : {}'.format(msg['info']))


@register_response
class Response_8010(Response):
    id = 0x8010
    descr = 'Version List'
    struct = OrderedDict([('major', 'int16'), ('installer', 'int16')])


@register_response
class Response_8015(Response):    
    id = 0x8015
    descr = 'Device List'
    struct = OrderedDict([('ID', 8), ('addr', 16), ('IEEE', 64), 
                          ('power_source', 'int8'), ('link_quality', 'int8'),
                          ('next', 'recursive')])

    def add_external_command(self):
        self.external_commands[ZGT_CMD_LIST_DEVICES] = msg


@register_response
class Response_8024(Response):
    id = 0x8024
    descr = 'Network joined / formed'
    struct = OrderedDict([('status', 'int8'), ('addr', 16), ('IEEE', 64), 
                          ('channel', 'int8')])

    def __init__(self, data):
        super().__init__()
        status_codes = {0: 'Joined existing network', 1: 'Formed new network'}
        self.status_text = status_codes.get(self.msg['status'], 'Failed with event code: %i' % self.msg['status'])

    def show_log(self):
        ZGT_LOG.debug('  * Status       : {}'.format(self.status_text))
        ZGT_LOG.debug('  - addr         : {}'.format(self.msg['addr']))
        ZGT_LOG.debug('  - IEEE         : {}'.format(self.msg['IEEE']))
        ZGT_LOG.debug('  - Channel      : {}'.format(self.msg['channel']))


@register_response
class Response_8045(Response):
    id = 0x8045
    descr = 'Active Endpoints List'
    struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                          ('endpoint_count', 'count'),
                          ('endpoint_list', 8)])

    def add_external_command(self):
        ep = [elt.decode() for elt in self.msg['endpoint_list']]
        self.external_commands[ZGT_CMD_LIST_ENDPOINTS] = {'addr': msg['addr'].decode(), 'endpoints': ep}

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        keys = [k for k in self.struct if key != 'endpoint_list']
        for key in keys:
            ZGT_LOG.debug('  - {:<25} : {}'.format(key, self.msg[key]))

        for i, ep in enumerate(msg['endpoint_list']):
            ZGT_LOG.debug('    * EndPoint %s : %s' % (i, ep))


@register_response
class Response_8100(Response):
    id = 0x8100
    descr = 'Attribute Report / Response'
    struct = OrderedDict([('sequence', 8),
                          ('short_addr', 16),
                          ('endpoint', 8),
                          ('cluster_id', 16),
                          ('attribute_id', 16),
                          ('attribute_status', 8),
                          ('attribute_type', 8),
                          ('attribute_size', 'len16'),
                          ('attribute_data', 'raw'),
                          ('end', 'rawend')])
   
    def __init__(self, data):
        super().__init__(data)
        self.attr_ref = (self.msg['cluster_id'],self.msg['attribute_id'])
        self.attr_dict = {}
        if ATTRIBUTES.get(self.attr_ref):
            self.attr_dict.update(ATTRIBUTES[self.attr_ref](self.msg['attribute_data']))
        else:
            ZGT_LOG.error('ATTRIBUTE NOT FOUND : {} / {}'.format(self.msg['cluster_id'],self.msg['attribute_id']))
         
    def show_log(self):
        super().show_log()
        ZGT_LOG.info('  - ATTTRIBUTES DETAILS')
        cluster_info = CLUSTERS.get(self.msg['cluster_id'], ZGT_CLUSTER_UNKNOWN)
        ZGT_LOG.info('    * {:<18} : {}'.format('cluster', cluster_info))
        for k, v in self.attr_dict.items():
            ZGT_LOG.info('    * {:<18} : {}'.format(k, v))
        ZGT_LOG.info('  - ATTTRIBUTES END')
            

@register_response
class Response_8102(Response_8100):
    id = 0x8102
    descr = 'Attribute Report / Response'


