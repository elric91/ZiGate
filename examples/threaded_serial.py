# Functions when used with serial & threads
class ThreadedConnection(object):
    def __init__(self, device, port='/dev/ttyUSB0'):
        import serial
        import threading

        self.device = device
        self.cnx = serial.Serial(port, 115200, timeout=0)
        self.thread = threading.Thread(target=self.read).start()
        device.send_to_transport = self.send

    def read(self):
        while True:
            bytesavailable = self.cnx.inWaiting()
            if bytesavailable > 0:
                self.device.read_data(self.cnx.read(bytesavailable))

    def send(self, data):
        self.cnx.write(data)


if __name__ == "__main__":
    import logging
    from pyzigate.interface import ZiGate
   
    # Setup logging on screen, debug mode
    l = logging.getLogger('zigate')
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler())

    # Thread base connection
    zigate = ZiGate()
    connection = ThreadedConnection(zigate)
    zigate.send_data('0015')
