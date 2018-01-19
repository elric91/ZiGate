from pyzigate.interface import ZiGate
import asyncio
import logging
from functools import partial


class AsyncWiFiConnection(object):

    def __init__(self, device, host, port=9999):
        loop = asyncio.get_event_loop()
        coro = loop.create_connection(ZiGateProtocol, host, port)
        futur = asyncio.run_coroutine_threadsafe(coro, loop)
        futur.add_done_callback(partial(self.bind_transport_to_device, device))
        loop.run_forever()
        loop.close()

    def bind_transport_to_device(self, device, protocol_refs):
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
            _LOGGER.debug('ERROR')

    def connection_lost(self, exc):
        pass


if __name__ == "__main__":

    zigate = ZiGate()

    # Asyncio based connection
    connection = AsyncWiFiConnection(zigate)

    zigate.send_data('0010')
