"""
Module that handles all interaction with the commandline.
"""
import argparse
import logging

from .environment import Environment
from .environment import generate_uuid

logger = logging.getLogger("Environment")


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
                        help=("Set the initial chrome window size. "
                              "eg 1920,1080"))
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
