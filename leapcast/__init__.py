"""
Leapcast turns your PC into a Chromecast server!

This enables you to stream video, audio, etc to your PC.
"""

__version__ = "2.0.0"
__url__ = "https://github.com/dz0ny/leapcast"
__author__ = "Janez Troha"
__email__ = "dz0ny@ubuntu.si"

import sys
from distutils.version import StrictVersion as StrictV

import logging

logger = logging.getLogger("Leapcast")

logger.setLevel(logging.INFO)

fmt_str = "[%(name)s: %(levelname)s] %(message)s"
formatter = logging.Formatter(fmt_str)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.propogate = False


# Check Python version.
current_version = StrictV(".".join([str(x) for x in sys.version_info[:3]]))

if sys.version_info[0] == 2 and not StrictV("2.7.0") <= current_version:
    msg = ("Leapcast for Python 2 requires Python 2.7.0 or higher. "
           "Found: Python " + str(current_version))

    sys.exit(msg)

elif sys.version_info[0] == 3 and not StrictV("3.3.0") <= current_version:
    msg = ("Leapcast for Python 3 requires Python 3.3.0 or higher. "
           "Found: Python " + str(current_version))

    sys.exit(msg)
