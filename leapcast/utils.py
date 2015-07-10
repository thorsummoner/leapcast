"""
Provides utility functions and classes used by Leapcast.
"""

import socket
import struct
from contextlib import closing as ctx_closing
from textwrap import dedent
from netifaces import interfaces, ifaddresses, AF_INET

from tornado.template import Template

SIOCGIFADDR = 0x8915


def render(template):
    """
    Renders a template using Tornado.
    """
    return Template(dedent(template))


def get_interface_address(if_name):
    """
    Returns the address of an interface.
    """
    import fcntl  # late import as this is only supported on Unix platforms.

    with ctx_closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
        return fcntl.ioctl(s.fileno(), SIOCGIFADDR,
                           struct.pack(b"256s", if_name[:15]))[20:24]


def get_remote_ip(address):
    """
    Returns the remote ip address.
    """
    # Create a socket to determine what address the client should
    # use
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(address)
    iface = s.getsockname()[0]
    s.close()
    return unicode(iface)


def get_own_ip():
    """
    Returns the best guess of what a good ip of this machine is on the network.
    """
    addresses = set()
    for ifname in interfaces():
        for iaddr in ifaddresses(ifname).setdefault(AF_INET, [{"addr": None}]):
            addresses.add(iaddr["addr"])

    addresses = [x for x in addresses if x is not None]

    if len(addresses) > 1:
        addresses = [x for x in addresses if x != "127.0.0.1"]

    if len(addresses) == 0:
        raise SystemError("Unable to automatically find address. "
                          "Specify address manually.")

    if len(addresses) != 1:
        raise SystemError("Got multiple candidate addresses, "
                          "specify address manually. "
                          "Candidates: {}".format(str(addresses)))

    return addresses[0]
