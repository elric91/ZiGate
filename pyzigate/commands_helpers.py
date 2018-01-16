class Mixin:
    """
    SubClass for the ZiGate class. Contains helper methods for command sending.
    """
    def read_attribute(self, device_address, device_endpoint, cluster_id, attribute_id):
        """
        Sends read attribute command to device

        :type self: Zigate
        :param str device_address: length 4. Example "AB01"
        :param str device_endpoint: length 2. Example "01"
        :param str cluster_id: length 4. Example "0000"
        :param str attribute_id: length 4. Example "0005"

        Examples:
        ========
        Replace device_address AB01 with your devices address.
        All clusters and parameters are not available on every device.
        - Get device manufacturer name: read_attribute('AB01', '01', '0000', '0004')
        - Get device name: read_attribute('AB01', '01', '0000', '0005')
        - Get device battery voltage: read_attribute('AB01', '01', '0001', '0006')
        """
        cmd = '02' + device_address + '01' + device_endpoint + cluster_id + '00 00 0000 01' + attribute_id
        self.send_data('0100', cmd)

    def read_multiple_attributes(self, device_address, device_endpoint, cluster_id, first_attribute_id, attributes):
        """
        Constructs read_attribute command with multiple attributes and sends it

        :type self: Zigate
        :param str device_address: length 4. E
        :param str device_endpoint: length 2.
        :param str cluster_id: length 4.
        :param str first_attribute_id: length 4
        :param int attributes: How many attributes are requested. Max value 255

        Examples:
        ========
        Replace device_address AB01 with your devices address.
        All clusters and parameters are not available on every device.

        - Get five first attributes from "General: Basic" cluster:
          read_multiple_attributes('AB01', '01', '0000', '0000', 5)
        """
        cmd = '02' + device_address + '01' + device_endpoint + cluster_id + '00 00 0000' + '{:02x}'.format(attributes)
        for i in range(attributes):
            cmd += '{:04x}'.format(int(first_attribute_id, 16) + i)
        self.send_data('0100', cmd)

    def permit_join(self):
        """
        permit join for 30 secs (1E)

        :type self: Zigate
        """
        self.send_data("0049", "FFFC1E00")
