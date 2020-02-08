#! /usr/bin/python3
import logging
from .parameters import * 
from collections import OrderedDict
from struct import unpack
from binascii import hexlify, unhexlify
from .conversions import zgt_decode_struct, zgt2int

ZGT_LOG = logging.getLogger('zigate')
ATTRIBUTES = {}

def register_attribute(cluster_id, attribute_id):
    def wrap(func):
        ATTRIBUTES[(cluster_id, attribute_id)] = func
    return wrap


#@register_attribute(b'0000', b'0005')
#def 
#

# Battery info
@register_attribute(b'0000', b'ff01')
def decode_xiaomi_info(data):
    if data != b'':
        struct = OrderedDict([('start', 16), ('battery', 16), ('end', 'rawend')])
        raw_info = unhexlify(zgt_decode_struct(struct, data)['battery'])
        battery_info = int(hexlify(raw_info[::-1]), 16)/1000
        return {'type':ZGT_BATTERY, 'value':battery_info, 'info':'Value : {} V'.format(battery_info)}
    else:
        return {'type':ZGT_BATTERY, 'value':0, 'info':'error'}

# simple button
@register_attribute(b'0006', b'0000')
def standard_button(data):
    if hexlify(data) == b'00':
        return {'type':ZGT_STATE_ON, 'value':'closed', 'info':'Closed/Taken off/Press'}
    else:
        return {'type':ZGT_STATE_OFF, 'value':'open', 'info':'Open/Release button'}

# multi button
@register_attribute(b'0006', '8000')
def multi_button(data):
    value = int(hexlify(attribute_data), 16)
    return {'type':ZGT_STATE_MULTI, 'value':value, 'info':'Multi clicks, pressed {} times'.format(value)}

# cube
@register_attribute(b'000c', b'0055')
def cube_horizontal_rotation_value(data):
    value = unpack('!f', data)[0]
    return {'type':'TBD', 'value':value, 'info':'Cube Horizontal Rotation Announce with value {}'.format(value)}

@register_attribute(b'000c', b'ff05')
def cube_horizontal_rotation_announce(data):
    value = hexlify(data)
    return {'type':'TBD', 'value':value, 'info':'Cube Horizontal Rotation Announce with value {}'.format(value)}

@register_attribute(b'0012', b'0055')
def cube_sliding_shaking(data):
    if hexlify(data) == b'0000':
        return {'type':'TBD', 'value':'shake', 'info':'Cube shaking'}
    elif data[0] == 2: # b'02xx'
        return {'type':'TBD', 'value':'tap{}'.format(data[1]), 'info':'Cube taping on face {}'.format(data[1])}
    elif data[0] == 1: # b'01xx'
        return {'type':'TBD', 'value':'slide{}'.format(data[1]), 'info':'sliding on face {}'.format(data[1])}
    elif data[0] == 0: # b'00xx' with xx != 00
        # binary format
        # aa : 01 = 90° 10 = 180°
        # bbb : face (from) number (if 180° always 000)
        # ccc : face (to) number
        rotation_info = [(data[1] >> i) & 1 for i in range(7, -1, -1)]
        rotation_info = ''.join([str(x) for x in rotation_info])
        rotation_type = int(rotation_info[0:2],2)
        rotation_from = int(rotation_info[2:5],2)
        rotation_to = int(rotation_info[5:8],2)
        if rotation_type == 2:
            return {'type':'TBD', 'value':'rotation180', 'info':'180° Rotation to face {}'.format(rotation_to)}
        else:
            return {'type':'TBD', 'value':'rotation90_from{}_to{}'.format(rotation_from, rotation_to), 'info':'90° Rotation from face {} to face {}'.format(rotation_from, rotation_to)}
    else:
        return {'type':'TBD', 'value':'error', 'info':'unknown'}

# Sensor (temp, humidity, pressure)
@register_attribute(b'0402', b'0000')
def genral_temperature(data):
    value = int.from_bytes(data, 'big', signed=True) / 100
    return {'type':ZGT_TEMPERATURE, 'value':value, 'info':'Temperature is {} °C'.format(value)}

@register_attribute(b'0403', b'0000')
def general_pressure(data):
    value = int(hexlify(data), 16)
    return {'type':ZGT_PRESSURE, 'value':value, 'info':'Pessure is {} mb'.format(value)}

@register_attribute(b'0403', b'0010')
def detailed_pressure(data):
    value = int(hexlify(data), 16)/10
    return {'type':ZGT_DETAILED_PRESSURE, 'value':value, 'info':'Pessure is {} mb'.format(value)}

@register_attribute(b'0403', b'0014')
def unknown_pressure(data):
    return {'type':'TBD', 'value':'unknown', 'info':'Pessure is unknown'}

@register_attribute(b'0405', b'0000')
def general_humidity(data):
    value = int(hexlify(data), 16) / 100
    return {'type':ZGT_HUMIDITY, 'value':value, 'info':'Humidity is {} %'.format(value)}

# Presence detection
@register_attribute(b'0406', b'0000')
def detect_presence(data):
    if hexlify(data) == b'01':
        return {'type':ZGT_EVENT, 'value':ZGT_EVENT_PRESENCE, 'info':'Presence detected'}
    
