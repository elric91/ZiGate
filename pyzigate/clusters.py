#! /usr/bin/python3
import logging
from .parameters import * 
from collections import OrderedDict
from .conversions import zgt_decode_struct, zgt2int

ZGT_LOG = logging.getLogger('zigate')
CLUSTERS = {}

def register_cluster(cluster):
    CLUSTERS[cluster.id] = cluster
    return cluster


class Cluster(object):
    id = None
    descr = 'Unknown Message'
    # {attribute_id: [ condition,
    #                  event_type,
    #                  event_value ]}
    params = dict()
    
    #def __init__(self, data):
        

