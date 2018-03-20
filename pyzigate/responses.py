#! /usr/bin/python3
import logging
from .parameters import * 
from collections import OrderedDict
from binascii import hexlify
from .conversions import zgt_decode_struct, zgt_to_int

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
        self.msg_type = zgt_to_int(data[0:2])
        self.msg_length = zgt_to_int(data[2:4])
        self.msg_crc = zgt_to_int(data[4:5])
        self.msg_data = data[5:]
        self.msg_rssi = zgt_to_int(data[-1:])
        
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
    struct = OrderedDict([('status', 'int'), ('sequence', 8),
                          ('packet_type', 16), ('info', 'rawend')])

    def __init__(self, data):
        Response.__init__(self, data)


    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        status_codes = {0: 'Success', 1: 'Invalid parameters',
                        2: 'Unhandled command', 3: 'Command failed',
                        4: 'Busy', 5: 'Stack already started'}
        status_text = status_codes.get(self.msg['status'], 'Failed with event code: %i' %
                                       self.msg['status'])

        ZGT_LOG.debug('  * Status              : {}'.format(status_text))
        ZGT_LOG.debug('  - Sequence            : {}'.format(self.msg['sequence']))
        ZGT_LOG.debug('  - Response to command : {}'.format(self.msg['packet_type']))
        if zgt_to_int(self.msg['info']) != 0x00:
            ZGT_LOG.debug('  - Additional msg: ', zgt_to_int(self.msg['info']))


@register_response
class Response_8015(Response):    
    id = 0x8015
    descr = 'Device List'
    struct = OrderedDict([('ID', 8), ('addr', 16), ('IEEE', 64), 
                          ('power_source', 'int8'), ('link_quality', 'int8'),
                          ('next', 'recursive')])
      

@register_response
class Response_8045(Response):
    id = 0x8045
    descr = 'Active Endpoints List'
    struct = OrderedDict([('sequence', 8), ('status', 8), ('addr', 16),
                          ('endpoint_count', 'count'),
                          ('endpoint_list', 8)])

    def add_external_command(self):
        ep = [elt.decode() for elt in self.msg['endpoint_list']]
        self.external_commands=[ZGT_CMD_LIST_ENDPOINTS] = {'addr': msg['addr'].decode(),
                                                           'endpoints': ep}

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {:04x} : {}'.format(self.id, self.descr))
        keys = [k for k in self.struct if key != 'endpoint_list']
        for key in keys:
            ZGT_LOG.debug('  - {:<25} : {}'.format(key, self.msg[key]))

        for i, ep in enumerate(msg['endpoint_list']):
            ZGT_LOG.debug('    * EndPoint %s : %s' % (i, ep))

     
