from abc import ABCMeta, abstractmethod

CLUSTERS = {b'0000': 'General: Basic',
            b'0001': 'General: Power Config',
            b'0002': 'General: Temperature Config',
            b'0003': 'General: Identify',
            b'0004': 'General: Groups',
            b'0005': 'General: Scenes',
            b'0006': 'General: On/Off',
            b'0007': 'General: On/Off Config',
            b'0008': 'General: Level Control',
            b'0009': 'General: Alarms',
            b'000A': 'General: Time',
            b'000F': 'General: Binary Input Basic',
            b'0020': 'General: Poll Control',
            b'0019': 'General: OTA',
            b'0101': 'General: Door Lock',
            b'0201': 'HVAC: Thermostat',
            b'0202': 'HVAC: Fan Control',
            b'0300': 'Lighting: Color Control',
            b'0400': 'Measurement: Illuminance',
            b'0402': 'Measurement: Temperature',
            b'0403': 'Measurement: Atmospheric Pressure',
            b'0405': 'Measurement: Humidity',
            b'0406': 'Measurement: Occupancy Sensing',
            b'0500': 'Security & Safety: IAS Zone',
            b'0702': 'Smart Energy: Metering',
            b'0B05': 'Misc: Diagnostics',
            b'1000': 'ZLL: Commissioning',
            b'FF01': 'Xiaomi private',
            b'FF02': 'Xiaomi private'
            }

class AbstractFeature(metaclass=ABCMeta):
    @abstractmethod
    def get_id(self):
        """

        :return:
        """
        pass

    @abstractmethod
    def get_name(self):
        pass

    def decode_msg(self, zigate, msg_type, msg_data):
        return False

    def interprete_attribute(self, zigate, device_addr, endpoint, attr_id, attr_type, size, data):
        return False
