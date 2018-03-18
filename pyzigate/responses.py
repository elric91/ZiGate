#! /usr/bin/python3
import logging
from .parameters import * 
from collections import OrderedDict
from .conversions import zgt_decode_struct

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
        self.msg_type = int.from_bytes(data[0:2], byteorder='big', signed=False)
        self.msg_length = int.from_bytes(data[2:4], byteorder='big', signed=False) 
        self.msg_crc = int.from_bytes(data[4:5], byteorder='big', signed=False)
        self.msg_data = data[5:]
        self.msg_rssi = int.from_bytes(data[-1:], byteorder='big', signed=False)
        
        self.msg = zgt_decode_struct(self.struct, self.msg_data)
        self.external_commands = OrderedDict()
        self.add_external_commands()

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {} : {}'.format(self.id, self.descr))
        for key in self.struct:
            ZGT_LOG.debug('  - {:>25} : {}'.format(key, self.msg[key]))
    
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
        ZGT_LOG.debug('RESPONSE {} : {}'.format(self.id, self.descr))
        status_codes = {0: 'Success', 1: 'Invalid parameters',
                        2: 'Unhandled command', 3: 'Command failed',
                        4: 'Busy', 5: 'Stack already started'}
        status_text = status_codes.get(self.msg['status'], 'Failed with event code: %i' %
                                       self.msg['status'])

        ZGT_LOG.debug('  * Status              : {}'.format(status_text))
        ZGT_LOG.debug('  - Sequence            : {}'.format(self.msg['sequence']))
        ZGT_LOG.debug('  - Response to command : {}'.format(self.msg['packet_type']))
        if int.from_bytes(self.msg['info'], byteorder='big', signed=False) != b'00':
            ZGT_LOG.debug('  - Additional self.msg: ', self.msg['info'])


@register_response
class Response_8015(Response):    
    id = 0x8015
    descr = 'Device List'
    struct = OrderedDict()

    def __init__(self, data):
        Response.__init__(self, data)
        self._log = []
        while True:
            struct = OrderedDict([('ID', 8), ('addr', 16), ('IEEE', 64), 
                                  ('power_source', 'int8'), ('link_quality', 'int8'),
                                  ('next', 'rawend')])
            
            msg = zgt_decode_struct(struct, self.msg_data)
            params = dict(msg)
            if params.get('next'):
                params.pop('next')
            self.external_commands[ZGT_CMD_LIST_DEVICES] = params

            self._log.append('  * deviceID     : {}'.format(msg['ID']))
            self._log.append('  - addr         : {}'.format(msg['addr']))
            self._log.append('  - IEEE         : {}'.format(msg['IEEE']))
            self._log.append('  - Power Source : {}'.format(msg['power_source']))
            self._log.append('  - Link Quality : {}'.format(msg['link_quality']))

            if len(msg['next']) < 13:
                break
            else:
                self.msg_data = msg['next']

    def show_log(self):
        ZGT_LOG.debug('RESPONSE {} : {}'.format(self.id, self.descr))
        for l in self._log:
            ZGT_LOG.info(l)
      

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
        ZGT_LOG.debug('RESPONSE {} : {}'.format(self.id, self.descr))
        keys = [k for k in self.struct if key != 'endpoint_list']
        for key in keys:
            ZGT_LOG.debug('  - {:>25} : {}'.format(key, self.msg[key]))

        for i, ep in enumerate(msg['endpoint_list']):
            ZGT_LOG.debug('    * EndPoint %s : %s' % (i, ep))

     
