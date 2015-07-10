"""
Provides the Environment object that contains information about the current
Leapcast environment.
"""

import logging

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
