# SubFunctions for the ZiGate class (self = ZiGate())
def interpret_attribute(self, msg_data):
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
    msg = self.decode_struct(struct, msg_data)
    device_addr = msg['short_addr']
    endpoint = msg['endpoint']
    cluster_id = msg['cluster_id']
    attribute_id = msg['attribute_id']
    attribute_size = msg['attribute_size']
    attribute_data = msg['attribute_data']
    self.set_device_property(device_addr, endpoint, ZGT_LAST_SEEN,
                             strftime('%Y-%m-%d %H:%M:%S'))

    if msg['sequence'] == b'00':
        _LOGGER.debug('  - Sensor type announce (Start after pairing 1)')
    elif msg['sequence'] == b'01':
        _LOGGER.debug('  - Something announce (Start after pairing 2)')

    # Device type
    if cluster_id == b'0000':
        if attribute_id == b'0005':
            self.set_device_property(device_addr, endpoint, 'type',
                                     attribute_data.decode())
            _LOGGER.info(' * type : {}'.format(attribute_data))
    # Button status
    elif cluster_id == b'0006':
        _LOGGER.info('  * General: On/Off')
        if attribute_id == b'0000':
            if hexlify(attribute_data) == b'00':
                self.set_device_property(device_addr, endpoint, ZGT_STATE,
                                         ZGT_STATE_ON)
                _LOGGER.info('  * Closed/Taken off/Press')
            else:
                self.set_device_property(device_addr, endpoint, ZGT_STATE,
                                         ZGT_STATE_OFF)
                _LOGGER.info('  * Open/Release button')
        elif attribute_id == b'8000':
            clicks = int(hexlify(attribute_data), 16)
            self.set_device_property(device_addr, endpoint, ZGT_STATE,
                                         ZGT_STATE_MULTI.format(clicks))
            _LOGGER.info('  * Multi click')
            _LOGGER.info('  * Pressed: {} times'.format(clicks))
    # Movement
    elif cluster_id == b'000c':  # Unknown cluster id
        _LOGGER.info('  * Rotation horizontal')
    elif cluster_id == b'0012':  # Unknown cluster id
        if attribute_id == b'0055':
            if hexlify(attribute_data) == b'0000':
                _LOGGER.info('  * Shaking')
            elif hexlify(attribute_data) == b'0055':
                _LOGGER.info('  * Rotating vertical')
                _LOGGER.info('  * Rotated: {}°'.
                             format(int(hexlify(attribute_data), 16)))
            elif hexlify(attribute_data) == b'0103':
                _LOGGER.info('  * Sliding')
    # Temperature
    elif cluster_id == b'0402':
        temperature = int(hexlify(attribute_data), 16) / 100
        self.set_device_property(device_addr, endpoint, ZGT_TEMPERATURE,
                                 temperature)
        _LOGGER.info('  * Measurement: Temperature'),
        _LOGGER.info('  * Value: {}'.format(temperature, '°C'))
    # Atmospheric Pressure
    elif cluster_id == b'0403':
        _LOGGER.info('  * Atmospheric pressure')
        pressure = int(hexlify(attribute_data), 16)
        if attribute_id == b'0000':
            self.set_device_property(device_addr, endpoint, ZGT_PRESSURE, pressure)
            _LOGGER.info('  * Value: {}'.format(pressure, 'mb'))
        elif attribute_id == b'0010':
            self.set_device_property(device_addr, endpoint,
                                     ZGT_DETAILED_PRESSURE, pressure/10)
            _LOGGER.info('  * Value: {}'.format(pressure/10, 'mb'))
        elif attribute_id == b'0014':
            _LOGGER.info('  * Value unknown')
    # Humidity
    elif cluster_id == b'0405':
        humidity = int(hexlify(attribute_data), 16) / 100
        self.set_device_property(device_addr, endpoint, ZGT_HUMIDITY, humidity)
        _LOGGER.info('  * Measurement: Humidity')
        _LOGGER.info('  * Value: {}'.format(humidity, '%'))
    # Presence Detection
    elif cluster_id == b'0406':
        # Only sent when movement is detected
        if hexlify(attribute_data) == b'01':
            self.set_device_property(device_addr, endpoint, ZGT_EVENT,
                                     ZGT_EVENT_PRESENCE)
            _LOGGER.debug('   * Presence detection')

    _LOGGER.info('  FROM ADDRESS      : {}'.format(msg['short_addr']))
    _LOGGER.debug('  - Source EndPoint : {}'.format(msg['endpoint']))
    _LOGGER.debug('  - Cluster ID      : {}'.format(msg['cluster_id']))
    _LOGGER.debug('  - Attribute ID    : {}'.format(msg['attribute_id']))
    _LOGGER.debug('  - Attribute type  : {}'.format(msg['attribute_type']))
    _LOGGER.debug('  - Attribute size  : {}'.format(msg['attribute_size']))
    _LOGGER.debug('  - Attribute data  : {}'.format(
                                           hexlify(msg['attribute_data'])))

