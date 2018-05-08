from platform import system, dist

class DockerMachine(object):
    def __init__(self):
        operating_system = system()
        if operating_system != 'Linux':
            raise UnsupportedOperatingSystem(operating_system)

    def install(self, verify=False):
        
