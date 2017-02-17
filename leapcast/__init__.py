from __future__ import unicode_literals

import sys

if not (2, 7) <= sys.version_info < (3,):
    sys.exit(
        'Leapcast requires Python >= 2.7, < 3, but found %s' %
        '.'.join(map(str, sys.version_info[:3])))

__version__ = '2.0.0'
__url__ = 'https://github.com/dz0ny/leapcast'
__author__ = 'Janez Troha'
__email__ = 'dz0ny@ubuntu.si'
