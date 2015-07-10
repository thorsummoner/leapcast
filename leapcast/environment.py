"""
Provides the Environment object that contains information about the current
Leapcast environment.
"""

import argparse
import logging
import uuid

from .chrome import get_chrome_path

logger = logging.getLogger("Environment")


class Environment(object):
    """
    Contains information about the current Leapcast environment.
    """
    channels = dict()
    global_status = dict()
    friendly_name = "leapcast"
    user_agent = ("Mozilla/5.0 (CrKey - 0.9.3) AppleWebKit/537.36 ?"
                  "(KHTML, like Gecko) Chrome/30.0.1573.2 Safari/537.36")
    chrome = get_chrome_path()
    fullscreen = False
    window_size = False
    interfaces = None
    uuid = None
    ips = []
    apps = None
    verbosity = logging.INFO


def parse_cmd():
    """
    Parses commandline arguments and configures the Leapcast environment.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true",
                        default=False, dest="debug", help="Debug")
    parser.add_argument("-i", "--interface", action="append",
                        dest="interfaces",
                        help=("Interface to bind to "
                              "(can be specified multiple times)"),
                        metavar="IPADDRESS")
    parser.add_argument("--name", help="Friendly name for this device")
    parser.add_argument("--user_agent", help="Custom user agent")
    parser.add_argument("--chrome", help="Path to Google Chrome executable")
    parser.add_argument("--fullscreen", action="store_true",
                        default=False, help="Start in full-screen mode")
    parser.add_argument("--window_size",
                        default=False,
                        help="Set the initial chrome window size. eg 1920,1080")
    parser.add_argument(
        "--ips", help="Allowed ips from which clients can connect")
    parser.add_argument("--apps", help="Add apps from JSON file")

    args = parser.parse_args()

    if args.debug:
        Environment.verbosity = logging.DEBUG
    logging.basicConfig(level=Environment.verbosity)

    if args.interfaces:
        Environment.interfaces = args.interfaces
        logger.debug("Interfaces is %s" % Environment.interfaces)

    if args.name:
        Environment.friendly_name = args.name
        logger.debug("Service name is %s" % Environment.friendly_name)

    if args.user_agent:
        Environment.user_agent = args.user_agent
        logger.debug("User agent is %s" % args.user_agent)

    if args.chrome:
        Environment.chrome = args.chrome
        logger.debug("Chrome path is %s" % args.chrome)

    if args.fullscreen:
        Environment.fullscreen = True

    if args.window_size:
        Environment.window_size = args.window_size

    if args.ips:
        Environment.ips = args.ips

    if args.apps:
        Environment.apps = args.apps

    if Environment.chrome is None:
        parser.error("could not locate chrome; use --chrome to specify one")

    generate_uuid()


def generate_uuid():
    """
    Generates an UUID and configures the Leapcast environment to use it.
    """
    Environment.uuid = str(uuid.uuid5(
        uuid.NAMESPACE_DNS, ("device.leapcast.%s" %
                             Environment.friendlyName).encode("utf8")))
