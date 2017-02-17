import os


def get_volume_controller():
    """Retrieve a VolumeController available on this platform. None, if no controller is available."""

    if os.path.exists("/usr/bin/amixer"):
        return ALSACtrl()

    return None


class VolumeController(object):
    """This abstract class specifies an interface to control the system volume."""

    def set_volume(self, level):
        raise Exception("Not implemented")

    def get_volume(self):
        raise Exception("Not implemented")

    def set_muted(self, mute):
        raise Exception("Not implemented")

    def mute(self):
        self.set_muted(True)

    def unmute(self):
        self.set_muted(False)

    def is_muted(self):
        raise Exception("Not implemented")


class ALSACtrl(VolumeController):
    """Implementation of VolumeController for ALSA."""

    def __init__(self):
        super(ALSACtrl, self).__init__()

    @staticmethod
    def _amixer(args):
        import subprocess
        p = subprocess.Popen(["/usr/bin/amixer"] + args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = p.communicate()
        assert p.wait() == 0

        vol_line = out.splitlines()
        vol_line = filter(lambda l: "Playback " in l, vol_line)
        vol_line = filter(lambda l: "%]" in l, vol_line)
        vol_line = filter(lambda l: "[o" in l, vol_line)
        assert len(vol_line) > 0
        vol_line = vol_line[0]

        volume, _, _ = vol_line.partition("%]")
        _, _, volume = volume.partition("[")
        volume = float(volume) / 100.0

        muted = "[off]" in vol_line
        return volume, muted

    def set_volume(self, level):
        v = "%d%%" % int(level * 100)
        ALSACtrl._amixer(["sset", "Master", v, "unmute"])

    def get_volume(self):
        volume, muted = ALSACtrl._amixer(["sget", "Master"])
        return volume

    def is_muted(self):
        volume, muted = ALSACtrl._amixer(["sget", "Master"])
        return muted

    def set_muted(self, mute):
        m = "mute" if mute else "unmute"
        ALSACtrl._amixer(["sset", "Master", m])
