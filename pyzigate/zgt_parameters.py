#! /usr/bin/python3
# Logging
import logging
ZGT_LOG = logging.getLogger('zigate')
ZGT_LOG.setLevel(logging.DEBUG)
# Force logging output to console
_LOGSTREAM = logging.StreamHandler()
_LOGSTREAM.setLevel(logging.DEBUG)
ZGT_LOG.addHandler(_LOGSTREAM)

# states & properties
ZGT_TEMPERATURE = 'temperature'
ZGT_PRESSURE = 'pressure'
ZGT_DETAILED_PRESSURE = 'detailed pressure'
ZGT_HUMIDITY = 'humidity'
ZGT_LAST_SEEN = 'last seen'
ZGT_EVENT = 'event'
ZGT_EVENT_PRESENCE = 'presence detected'
ZGT_STATE = 'state'
ZGT_STATE_ON = 'on-press'
ZGT_STATE_MULTI = 'multi_{}'
ZGT_STATE_OFF = 'off-release'

# commands for external use
ZGT_CMD_NEW_DEVICE = 'new device'
ZGT_CMD_LIST_ENDPOINTS = 'list endpoints'
