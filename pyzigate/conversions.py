#! /usr/bin/python3

import logging
from binascii import hexlify
from collections import OrderedDict

ZGT_LOG = logging.getLogger('zigate')


def zgt_encode(data):
        """encode all characters < 0x02 to avoid """
        encoded = []
        for x in data:
            if x < 0x10:
                encoded.extend([0x02, x ^ 0x10])
            else:
                encoded.append(x)
        return encoded

def zgt_decode(data):
    """reverse of zigate_encode to get back the real message"""
    encoded = False
    decoded_data = b''

    def bxor_join(b1, b2):  # use xor for bytes
        parts = []
        for b1, b2 in zip(b1, b2):
            parts.append(bytes([b1 ^ b2]))
        return b''.join(parts)

    for x in data:
        if bytes([x]) == b'\x02':
            encoded = True
        elif encoded is True:
            encoded = False
            decoded_data += bxor_join(bytes([x]), b'\x10')
        else:
            decoded_data += bytes([x])

    return decoded_data


def zgt_checksum(cmd, length, data):
    tmp = 0
    tmp ^= cmd[0]
    tmp ^= cmd[1]
    tmp ^= length[0]
    tmp ^= length[1]
    if data:
        for x in data:
            tmp ^= x

    return tmp

def zgt2int(data):
    return int.from_bytes(data, byteorder='big', signed=False)


def zgt_decode_struct(struct, msg, elt_id=0):
    output = OrderedDict()
    iter_struct = struct.copy()
    # recursive if the last element says so
    is_recursive = list(struct.items())[-1][1] == 'recursive'
        
    while iter_struct:
        key, elt_type = iter_struct.popitem(last=False)
        if is_recursive: # if recursive, index the keys
            key = '{1}[{0:02x}]'.format(elt_id, key)

        # uint_8, 16, 32, 64 ... or predefined byte length
        if type(elt_type) == int:
            length = int(elt_type / 8)
            output[key] = hexlify(msg[:length])
            msg = msg[length:]
        # int (1 ou 2 bytes)
        elif elt_type in ('int', 'int8', 'int16'):
            if elt_type == 'int16':
                index = 2
            else:
                index = 1
            output[key] = int(hexlify(msg[:index]), 16)
            msg = msg[index:]
        # element gives length of next element in message
        # (which could be raw)
        elif elt_type in ('len8', 'len16'):
            if elt_type == 'len16':
                index = 2
            else:
                index = 1
            length = int(hexlify(msg[0:index]), 16)
            output[key] = length
            msg = msg[index:]
            # let's get the next element
            key, elt_type = iter_struct.popitem(last=False)
            if elt_type == 'raw':
                output[key] = msg[:length]
                msg = msg[length:]
            else:
                output[key] = hexlify(msg[:length])
                msg = msg[length:]
        # element gives number of next elements
        # (which can be of a defined length)
        elif elt_type == 'count':
            count = int(hexlify(msg[:1]), 16)
            output[key] = count
            msg = msg[1:]
            # let's get the next element
            # (list of elements referenced by the count)
            key, elt_type = iter_struct.popitem(last=False)
            output[key] = []
            length = int(elt_type / 8)
            for i in range(count):
                output[key].append(hexlify(msg[:length]))
                msg = msg[length:]
        # remaining of the message
        elif elt_type == 'end':
            output[key] = hexlify(msg)
        # remaining of the message as raw data
        elif elt_type == 'rawend':
            output[key] = msg
        elif elt_type == 'recursive' and len(msg) > 2:
            next_output = zgt_decode_struct(struct, msg, elt_id + 1)
            output.update(next_output)

    return output

