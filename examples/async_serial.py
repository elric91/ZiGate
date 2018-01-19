from pyzigate.interface import ZiGate
import asyncio
import serial_asyncio
import logging
from functools import partial


class AsyncSerialConnection(object):

    def __init__(self, device, port='/dev/ttyUSB0'):
        loop = asyncio.get_event_loop()
        coro = serial_asyncio.create_serial_connection(loop, ZiGateProtocol, port, baudrate=115200)
        futur = asyncio.run_coroutine_threadsafe(coro, loop)  # Requires python 3.5.1
        futur.add_done_callback(partial(self.bind_transport_to_device, device))
        loop.run_forever()
        loop.close()

    @staticmethod
    def bind_transport_to_device(device, protocol_refs):
        """
        Bind device and protocol / transport once they are ready
        Update the device status @ start
        """
        transport = protocol_refs.result()[0]
        protocol = protocol_refs.result()[1]
        protocol.device = device
        device.send_to_transport = transport.write


class ZiGateProtocol(asyncio.Protocol):
    def __init__(self):
        super().__init__()
        self.transport = None
        self._logger = logging.getLogger(self.__module__)
        self._logger.setLevel(logging.DEBUG)

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        try:
            self.device.read_data(data)
        except:
            self._logger.debug('ERROR')

    def connection_lost(self, exc):
        pass


if __name__ == "__main__":

    zigate = ZiGate()

    # Asyncio based connection
    connection = AsyncSerialConnection(zigate)

    zigate.send_data('0010')
