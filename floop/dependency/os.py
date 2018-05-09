from platform import system

_FLOOP_SUPPORTED_OPERATING_SYSTEMS = ['linux']

class UnsupportedOperatingSystem(Exception):
    pass

def check_os():
    operating_system = system().lower()
    if operating_system not in _FLOOP_SUPPORTED_OPERATING_SYSTEMS:
        raise UnsupportedOperatingSystem(operating_system)
