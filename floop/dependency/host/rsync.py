from platform import system
from floop.util.syscall import syscall

class Rsync(object):
    def __init__(self):
        operating_system = system()
        if operating_system != 'Linux':
            raise UnsupportedOperatingSystem(operating_system)

    def install(self, verify=False):
        self.__install_apt_packages()
        if verify:
            self.__verify()

    def __install_apt_packages():
        apt_update = 'apt-get update'
        apt_install = 'apt-get install -y rsync' 
        commands = [apt_update, apt_install]
        for command in commands:
            print(command)
            syscall(command, check=True)

    def __verify(self):
       check_version = 'rsync --version'
       syscall(check_version, check=True)
