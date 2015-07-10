"""
Module related to finding and interacting with Google Chrome / Chromium.
"""

import sys
import os
import glob


def get_chrome_path():
    """
    Returns the first available path to a Google Chrome / Chromium executable.
    """
    if sys.platform == "win32":
        # First path includes fallback for Windows XP, because it doesn"t have
        # LOCALAPPDATA variable.
        globs = [
            os.path.join(
                os.getenv("LOCALAPPDATA", os.path.join(
                    os.getenv("USERPROFILE"),
                    "Local Settings\\Application Data"
                )),
                "Google\\Chrome\\Application\\chrome.exe"
            ),

            os.path.join(os.getenv("ProgramW6432", "C:\\Program Files"),
                         "Google\\Chrome\\Application\\chrome.exe"),

            os.path.join(os.getenv("ProgramFiles(x86)",
                                   "C:\\Program Files (x86)"),
                         "Google\\Chrome\\Application\\chrome.exe")
        ]

    elif sys.platform == "darwin":
        globs = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]

    else:
        globs = [
            "/usr/bin/google-chrome",
            "/opt/google/chrome/google-chrome",
            "/opt/google/chrome-*/google-chrome",
            "/usr/bin/chromium-browser"
        ]

    for g in globs:
        for path in glob.glob(g):
            if os.path.exists(path):
                return path
