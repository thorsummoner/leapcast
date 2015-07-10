#!/usr/bin/env python

"""
This is the main point-of-entry for Leapcast.
"""

import signal
import logging
import sys
from os import environ

from leapcast.environment import parse_cmd, Environment
from leapcast.services.leap import LEAPserver
from leapcast.services.mdns import MDNSServer
from leapcast.services.ssdp import SSDPserver


logger = logging.getLogger('Leapcast')


def main():
    """
    Starts the Leapcast server.
    """
    parse_cmd()

    if sys.platform == 'darwin' and environ.get('TMUX') is not None:
        logger.error('Running Chrome inside tmux on OS X might cause problems.'
                     ' Please start leapcast outside tmux.')
        sys.exit(1)

    def shutdown(signum, frame):
        """
        Called when a SIGTERM or SIGINT signal is received.

        Shuts down the Leapcast server.
        """
        leap_server.sig_handler(signum, frame)
        mdns_server.shutdown()
        ssdp_server.shutdown()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    mdns_server = MDNSServer()
    mdns_server.start(interfaces=Environment.interfaces or [])

    ssdp_server = SSDPserver()
    ssdp_server.start(Environment.interfaces)

    leap_server = LEAPserver()
    leap_server.start()


if __name__ == "__main__":
    main()
