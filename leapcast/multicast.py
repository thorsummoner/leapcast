"""
Provicdes the MulticastServer class and other multicast-related things.
"""

import struct
import socket
import operator

import logging

from six.moves.socketserver import ThreadingUDPServer

from .mixins import ControlMixin
from .utils import get_interface_address


class MulticastServer(ControlMixin, ThreadingUDPServer):
    """
    A Multicast Server.
    """
    allow_reuse_address = True

    def __init__(self, addr, handler, poll_interval=0.5,
                 bind_and_activate=True, interfaces=None):
        ThreadingUDPServer.__init__(self, ("", addr[1]),
                                    handler,
                                    bind_and_activate)
        ControlMixin.__init__(self, handler, poll_interval)
        self._multicast_address = addr
        self._listen_interfaces = interfaces
        self.set_loopback_mode(1)  # localhost
        self.set_ttl(255)  # all networks
        self.handle_membership(socket.IP_ADD_MEMBERSHIP)

    def set_loopback_mode(self, mode):
        """
        Sets the loopback mode of the Multicast Server.
        """
        mode = struct.pack("b", operator.truth(mode))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP,
                               mode)

    def server_bind(self):
        """
        Binds the server to a socket.
        """
        try:
            if hasattr(socket, "SO_REUSEADDR"):
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception as e:
            logging.log(e)
        try:
            if hasattr(socket, "SO_REUSEPORT"):
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception as e:
            logging.log(e)
        ThreadingUDPServer.server_bind(self)

    def handle_membership(self, cmd):
        """
        Handles Multicast membership.
        """
        if self._listen_interfaces is None:
            mreq = struct.pack(
                str("4sI"), socket.inet_aton(self._multicast_address[0]),
                socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP,
                                   cmd, mreq)
        else:
            for interface in self._listen_interfaces:
                try:
                    if_addr = socket.inet_aton(interface)
                except socket.error:
                    if_addr = get_interface_address(interface)
                mreq = socket.inet_aton(self._multicast_address[0]) + if_addr
                self.socket.setsockopt(socket.IPPROTO_IP,
                                       cmd, mreq)

    def set_ttl(self, ttl):
        """
        Sets the TTL
        """
        ttl = struct.pack("B", ttl)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def server_close(self):
        """
        Called when the server closes.

        Ensures the Multicast membership is dropped.
        """
        self.handle_membership(socket.IP_DROP_MEMBERSHIP)
