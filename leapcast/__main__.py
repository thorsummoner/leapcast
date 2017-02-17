#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import unicode_literals

import signal
import logging
import sys
from os import environ

from leapcast.environment import parse_cmd, Environment
from leapcast.services.leap import LEAPserver
from leapcast.services.mdns import MDNSserver
from leapcast.services.ssdp import SSDPserver


logger = logging.getLogger('Leapcast')


def main():
    parse_cmd()

    if sys.platform == 'darwin' and environ.get('TMUX') is not None:
        logger.error('Running Chrome inside tmux on OS X might cause problems.'
                     ' Please start leapcast outside tmux.')
        sys.exit(1)

    def shutdown(signum, frame):
        leap_server.sig_handler(signum, frame)
        mdns_server.shutdown()
        ssdp_server.shutdown()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    mdns_server = MDNSserver()
    mdns_server.start(Environment.interfaces)

    ssdp_server = SSDPserver()
    ssdp_server.start(Environment.interfaces)

    leap_server = LEAPserver()
    leap_server.start()


if __name__ == "__main__":
    main()
