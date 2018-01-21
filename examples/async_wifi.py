import asyncio
import threading
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

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        try:
            self.device.read_data(data)
        except:
            ZGT_LOG.debug('ERROR')

    def connection_lost(self, exc):
        pass


def start_loop(loop):
    loop.run_forever()
    loop.close()    


if __name__ == "__main__":
    import logging
    from pyzigate.interface import ZiGate
   
    # Setup logging on screen, debug mode
    l = logging.getLogger('zigate')
    l.setLevel(logging.DEBUG)
    l.addHandler(logging.StreamHandler())


    # Asyncio based connection
    zigate = ZiGate()
    loop = asyncio.get_event_loop()
    connection = AsyncWiFiConnection(zigate)

    # Adding loop in a thread for testing purposes (i.e non blocking ipython console)
    # not needed when full program is run within the event loop
    t = threading.Thread(target=start_loop, args=(loop,))
    t.start()

    zigate.send_data('0010')
