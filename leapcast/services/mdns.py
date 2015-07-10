from zeroconf import ServiceInfo, Zeroconf
import socket

from ..utils import get_own_ip


class MDNSServer(object):
    TYPE = "_googlecast._tcp.local"

    DESCRIPTION = {
        "id": "99e46e880f89a46ae627f2e75278cb46",
        "ve": "02",
        "md": "Chromecast",
        "ic": "/setup/icon.png"
    }

    WEIGHT = 0
    PRIORITY = 0

    def __init__(self, *args, **kwargs):
        self.name = "leapcast"
        self.server = None
        self.address = None
        self.port = None

    def _get_dns_name(self):
        return "{}.{}".format(self.name, self.TYPE)

    def _get_dns_server(self):
        return "{}.local".format(self.name)

    def start(self, address=None, port=8009, interfaces=[]):
        self.server = Zeroconf(interfaces)

        if address is None:
            address = get_own_ip()

        self.address = socket.inet_aton(address)
        self.port = port

        self.info = ServiceInfo(self.TYPE, self._get_dns_name(), self.address,
                                self.port, self.WEIGHT, self.PRIORITY,
                                self.DESCRIPTION, self._get_dns_server())

        self.server.register_service(self.info)

    def shutdown(self):
        self.server.unregister_service(self.info)
        self.server.close()
